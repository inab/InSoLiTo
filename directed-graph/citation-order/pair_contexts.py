"""Show how two tools are cited together, with the paragraphs that cite them.

Finds the articles that cite a paper of both tools (bio.tools IDs; papers
matched by DOI, PMID or PMCID as in step 1) and counts them by how close the
two citations are and which tool is cited first. Delta and tool gap come
from the outputs of steps 3 to 5 in EDGES (research articles, order of the
references in SECTION):
  - the two edges from directed_edges.csv (articles, share, medians, sums)
  - delta and tool gap per article from directed_edges_raw.parquet, signed
    from tool_a to tool_b (positive when tool_a is cited first)
  - the position of every tool per article from tool_order.parquet
For 15 articles, split across the groups by their size, downloads the full text from Europe PMC and
writes data/pair_contexts/<tool_a>__<tool_b>.html: the edges, histograms of
both distances over all the articles, then, per sampled article, a strip with the
position of every tool cited in SECTION and the paragraphs that cite either
tool, with the citations of each tool highlighted in its own colour. The XML
is cached in data/pair_contexts/xml/.

Run from BH2026-InSoLiTo/:
    .venv/bin/python directed-graph/citation-order/pair_contexts.py star deseq2
"""

import argparse
import html
import sys
import urllib.request
from pathlib import Path

import duckdb
from lxml import etree

sys.path.insert(0, 'directed-graph/europepmc')
import parse_jats as pj  # noqa: E402

BIOTOOLS = 'directed-graph/biotools/data/biotools_publications.csv'
OUT_DIR = Path('directed-graph/citation-order/data/pair_contexts')
GROUPS = ['same sentence', 'same paragraph', 'different paragraphs']
N_SAMPLE = 15  # articles shown in total, split across the groups by their size
# Outputs of steps 3 to 5, and the SECTION that 03_order_tools.py used for them.
EDGES = 'directed-graph/edges-processed'
SECTION = 'methods'
MAX_DELTA, MAX_GAP = 20, 10  # histogram range; larger distances go in the end bars

ap = argparse.ArgumentParser()
ap.add_argument('tool_a')
ap.add_argument('tool_b')
ap.add_argument('--export', default='directed-graph/europepmc/data/export',
                help='folder with the Parquet tables')
args = ap.parse_args()
a, b = args.tool_a.lower(), args.tool_b.lower()
EXPORT = args.export
(OUT_DIR / 'xml').mkdir(parents=True, exist_ok=True)

con = duckdb.connect()

# Every in-text citation of a paper of either tool.
con.execute(f"""
    CREATE TEMP TABLE m AS
    WITH v AS (SELECT * FROM '{BIOTOOLS}' WHERE biotoolsID IN ($a, $b)),
    tool_works AS (
        SELECT v.biotoolsID AS tool, w.work_id FROM v JOIN '{EXPORT}/works.parquet' w
            ON lower(v.doi) = w.doi OR CAST(v.pmid AS VARCHAR) = CAST(w.pmid AS VARCHAR)
                                    OR CAST(v.pmcid AS VARCHAR) = CAST(w.pmcid AS VARCHAR)
    )
    SELECT DISTINCT m.pmcid, t.tool, m.ref_id, m.mention_idx, m.sec_title, m.block_idx, m.sentence_idx
    FROM '{EXPORT}/mentions.parquet' m
    JOIN '{EXPORT}/citations.parquet' c USING (pmcid, ref_id)
    JOIN tool_works t USING (work_id)
""", {'a': a, 'b': b})

# One row per article citing both: closest relation and which tool comes first.
con.execute("""
    CREATE TEMP TABLE art AS
    SELECT x.pmcid,
           CASE WHEN bool_or(x.sentence_idx = y.sentence_idx) THEN 'same sentence'
                WHEN bool_or(x.block_idx = y.block_idx) THEN 'same paragraph'
                ELSE 'different paragraphs' END AS relation,
           min(x.mention_idx) < min(y.mention_idx) AS a_first
    FROM m x JOIN m y ON x.pmcid = y.pmcid AND x.tool = $a AND y.tool = $b
    GROUP BY 1
""", {'a': a, 'b': b})

# Steps 3 to 5: position of every tool in each kept article (tool_order),
# delta and tool gap per article (directed_edges_raw) and the edge numbers
# (directed_edges). Signed here from tool_a to tool_b: positive when tool_a is
# cited first. Articles not kept in step 2, or not citing both tools in
# SECTION, have no row and no delta.
con.execute(f"""
    CREATE TEMP TABLE tools AS
    SELECT pmcid, biotoolsID AS tool, first_rank,
           dense_rank() OVER (PARTITION BY pmcid ORDER BY first_rank) AS tool_rank
    FROM '{EDGES}/tool_order.parquet' JOIN art USING (pmcid)
""")
con.execute(f"""
    CREATE TEMP TABLE dist AS
    SELECT pmcid, CASE WHEN source = $a THEN delta ELSE -delta END AS delta,
           CASE WHEN source = $a THEN tool_gap ELSE -tool_gap END AS tool_gap
    FROM '{EDGES}/directed_edges_raw.parquet'
    WHERE (source = $a AND target = $b) OR (source = $b AND target = $a)
""", {'a': a, 'b': b})
edges = con.execute(f"""
    SELECT source, target, n_articles, share_forward, median_delta, median_tool_gap,
           sum_inv_delta, sum_inv_tool_gap
    FROM '{EDGES}/directed_edges.csv' WHERE (source, target) IN (($a, $b), ($b, $a))
    ORDER BY source = $b
""", {'a': a, 'b': b}).fetchall()
# Number of references cited in SECTION, only for the scale of the strips.
con.execute(f"""
    CREATE TEMP TABLE n_refs AS
    SELECT pmcid, count(DISTINCT ref_id) AS n_refs FROM '{EXPORT}/mentions.parquet' JOIN dist USING (pmcid)
    WHERE sec_class = ? AND in_table IS NOT TRUE AND in_caption IS NOT TRUE
    GROUP BY pmcid
""", [SECTION])


def paragraphs(pmcid):
    """Paragraphs of the article by block_idx, numbered as parse_jats.py does."""
    path = OUT_DIR / 'xml' / f'{pmcid}.xml'
    if not path.exists():
        url = f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML'
        path.write_bytes(urllib.request.urlopen(url, timeout=60).read())
    root = etree.fromstring(path.read_bytes(), etree.XMLParser(recover=True, huge_tree=True,
                                                               resolve_entities=False))
    blocks = {}

    class Walker(pj.Walker):
        def walk(self, el, ctx, depth=0):
            if pj.localname(el) in pj.BLOCK_TAGS:
                blocks[self.n_blocks] = el  # the block_idx walk() is about to give it
            super().walk(el, ctx, depth)

    Walker({}, {}, {}).walk(root.find('.//body'), pj.Ctx())
    return pj.text_of(root.find('.//article-meta//article-title')), blocks


def text(el, rid_tool):
    """HTML of an element, with the tools' citations highlighted."""
    s = html.escape(el.text or '') + ''.join(
        ('' if pj.localname(c) in pj.SKIP_TAGS else text(c, rid_tool)) + html.escape(c.tail or '')
        for c in el)
    tools = [rid_tool[r] for r in (el.get('rid') or '').split() if r in rid_tool]
    if pj.localname(el) == 'xref' and tools:
        s = f'<mark class="{"a" if tools[0] == a else "b"}" title="{tools[0]}">{s.strip()}</mark>'
    return s


def histogram(values, limit, label):
    """SVG bar chart of signed distances, clipped to [-limit, limit]."""
    counts = {}
    for v in values:
        k = max(-limit, min(limit, v))
        counts[k] = counts.get(k, 0) + 1
    if not counts:
        return f'<p class="muted">No article cites both tools in {SECTION}.</p>'
    w, h, pad = 640, 170, 24
    bw = (w - 2 * pad) / (2 * limit + 1)
    top = max(counts.values())
    bars = []
    for k, n in sorted(counts.items()):
        bh = (h - 2 * pad) * n / top
        x = pad + (k + limit) * bw
        cls = 'a' if k > 0 else 'b' if k < 0 else 'z'
        edge = '≤' if k == -limit else '≥' if k == limit else ''
        bars.append(f'<rect class="{cls}" x="{x + 1:.1f}" y="{h - pad - bh:.1f}" width="{bw - 2:.1f}" '
                    f'height="{bh:.1f}"><title>{label} {edge}{k}: {n} articles</title></rect>')
    ticks = ''.join(f'<text x="{pad + (k + limit + 0.5) * bw:.1f}" y="{h - 8}">{k}</text>'
                    for k in range(-limit, limit + 1, max(1, limit // 5)))
    return (f'<svg viewBox="0 0 {w} {h}" class="hist" role="img" aria-label="{label} histogram">'
            f'{"".join(bars)}<line x1="{pad}" x2="{w - pad}" y1="{h - pad}" y2="{h - pad}"/>{ticks}'
            f'<text x="{pad}" y="12" class="lab">{top} articles</text></svg>')


def strip(pmcid):
    """SVG with the position of each tool among the references of SECTION."""
    row = con.execute('SELECT n_refs, delta, tool_gap FROM dist JOIN n_refs USING (pmcid) WHERE pmcid = ?',
                      [pmcid]).fetchone()
    if row is None:
        return (f'<p class="muted">No delta: not a research article kept in step 2, '
                f'or not citing both tools in {SECTION}.</p>')
    n_refs, delta, gap = row
    rows = con.execute('SELECT tool, first_rank FROM tools WHERE pmcid = ? ORDER BY first_rank',
                       [pmcid]).fetchall()
    w, pad = 640, 12
    x = lambda r: pad + (w - 2 * pad) * (r - 0.5) / n_refs  # noqa: E731
    marks = []
    for tool, r in rows:
        cls = 'a' if tool == a else 'b' if tool == b else 'o'
        y1 = 10 if cls != 'o' else 18
        marks.append(f'<line class="{cls}" x1="{x(r):.1f}" x2="{x(r):.1f}" y1="{y1}" y2="38">'
                     f'<title>{tool}: reference {r}</title></line>')
        if cls != 'o':
            marks.append(f'<text class="{cls}" x="{x(r):.1f}" y="52">{tool}</text>')
    ra, rb = (r for t in (a, b) for tool, r in rows if tool == t)
    span = f'<line class="span" x1="{x(ra):.1f}" x2="{x(rb):.1f}" y1="28" y2="28"/>'
    return (f'<p class="dist">delta <b>{delta:+d}</b> · tool gap <b>{gap:+d}</b> · '
            f'{len({r for _, r in rows})} of the {n_refs} references in {SECTION} are tool papers</p>'
            f'<svg viewBox="0 0 {w} 58" class="strip" role="img" aria-label="tool positions">'
            f'<line class="axis" x1="{pad}" x2="{w - pad}" y1="38" y2="38"/>{span}{"".join(marks)}</svg>')


# Share N_SAMPLE across the groups by their size (largest remainder).
sizes = dict(con.execute('SELECT relation, count(*) FROM art GROUP BY 1').fetchall())
total = sum(sizes.values())
quota = {g: N_SAMPLE * sizes.get(g, 0) / total if total else 0 for g in GROUPS}
shown = {g: int(q) for g, q in quota.items()}
for g in sorted(GROUPS, key=lambda g: quota[g] - shown[g], reverse=True)[:min(N_SAMPLE, total) - sum(shown.values())]:
    shown[g] += 1

body = []
summary = []
for group in GROUPS:
    n, n_a_first = con.execute('SELECT count(*), count(*) FILTER (WHERE a_first) FROM art WHERE relation = ?',
                               [group]).fetchone()
    summary.append(f'<tr><td>{group}</td><td>{n}</td><td>{n_a_first}</td><td>{n - n_a_first}</td></tr>')
    print(f'{group}: {n} articles, {a} cited first in {n_a_first}, {b} in {n - n_a_first}')
    body.append(f'<h2>{group.capitalize()} <span class="muted">({n:,} articles, {shown[group]} shown)</span></h2>')
    sample = con.execute('SELECT pmcid, a_first FROM art WHERE relation = ? ORDER BY hash(pmcid) LIMIT ?',
                         [group, shown[group]]).fetchall()
    for pmcid, a_first in sample:
        title, blocks = paragraphs(pmcid)
        first = a if a_first else b
        body.append(f'<article><h3><a href="https://europepmc.org/article/PMC/{pmcid}">{pmcid}</a> '
                    f'{html.escape(title)}</h3><p class="muted">First cited in the text: '
                    f'<mark class="{"a" if a_first else "b"}">{first}</mark></p>{strip(pmcid)}')
        rows = con.execute('SELECT tool, ref_id, block_idx, sec_title FROM m WHERE pmcid = ? ORDER BY mention_idx',
                           [pmcid]).fetchall()
        rid_tool = {ref_id: tool for tool, ref_id, _, _ in rows}
        for block_idx, sec_title in dict.fromkeys((r[2], r[3]) for r in rows):
            body.append(f'<h4>{html.escape(sec_title or "")}</h4><p>{text(blocks[block_idx], rid_tool)}</p>')
        body.append('</article>')

dists = con.execute('SELECT delta, tool_gap FROM dist WHERE delta IS NOT NULL').fetchall()
deltas, gaps = [d for d, _ in dists], [g for _, g in dists]
n_art = con.execute('SELECT count(*) FROM art').fetchone()[0]
where = SECTION
cls = {a: 'a', b: 'b'}
edge_rows = ''.join(
    f'<tr><td><mark class="{cls[src]}">{src}</mark> → <mark class="{cls[tgt]}">{tgt}</mark></td><td>{n}</td>'
    f'<td>{share:.2f}</td><td>{md:g}</td><td>{mg:g}</td><td>{sd:.1f}</td><td>{sg:.1f}</td></tr>'
    for src, tgt, n, share, md, mg, sd, sg in edges) or '<tr><td colspan="7">No edge in directed_edges.csv</td></tr>'
page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{a} and {b}</title>
<style>
:root {{ --bg: #fff; --fg: #1f2328; --muted: #6b7280; --line: #d0d7de;
        --a: #2563eb; --a-bg: #dbeafe; --b: #c2410c; --b-bg: #ffedd5; --o: #9ca3af; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg: #16181d; --fg: #e6e6e6; --muted: #9aa0a6; --line: #3a3f47;
          --a: #60a5fa; --a-bg: #1e3a8a; --b: #fb923c; --b-bg: #7c2d12; --o: #6b7280; }} }}
body {{ background: var(--bg); color: var(--fg); font: 15px/1.55 system-ui, sans-serif;
       max-width: 860px; margin: 0 auto; padding: 16px; }}
a {{ color: inherit; }}
mark {{ border-radius: 3px; padding: 0 2px; color: inherit; }}
mark.a {{ background: var(--a-bg); box-shadow: inset 0 -2px var(--a); }}
mark.b {{ background: var(--b-bg); box-shadow: inset 0 -2px var(--b); }}
.muted {{ color: var(--muted); font-weight: normal; }}
article {{ border-top: 1px solid var(--line); padding: 8px 0 16px; }}
h3 {{ font-size: 16px; margin-bottom: 4px; }} h4 {{ margin: 12px 0 0; color: var(--muted); font-size: 13px; }}
table {{ border-collapse: collapse; }} td, th {{ border-bottom: 1px solid var(--line); padding: 4px 12px 4px 0; text-align: left; }}
svg {{ width: 100%; height: auto; display: block; }}
svg text {{ font-size: 11px; fill: var(--muted); text-anchor: middle; }} svg text.lab {{ text-anchor: start; }}
svg line {{ stroke: var(--line); }} svg .axis {{ stroke: var(--muted); }}
rect.a {{ fill: var(--a); }} rect.b {{ fill: var(--b); }} rect.z {{ fill: var(--o); }}
.strip line {{ stroke-width: 2; }} .strip line.o {{ stroke: var(--o); }}
.strip line.a {{ stroke: var(--a); stroke-width: 3; }} .strip line.b {{ stroke: var(--b); stroke-width: 3; }}
.strip line.span {{ stroke: var(--muted); stroke-dasharray: 3 3; }}
.strip text.a {{ fill: var(--a); }} .strip text.b {{ fill: var(--b); }}
.dist {{ margin: 4px 0 0; font-size: 13px; }}
</style></head><body>
<h1><mark class="a">{a}</mark> and <mark class="b">{b}</mark></h1>
<p>{n_art} articles cite both tools, grouped by the closest
pair of citations. {sum(shown.values())} articles are shown below, split across the groups by their size.</p>
<table><tr><th>Group</th><th>Articles</th><th>{a} first</th><th>{b} first</th></tr>{''.join(summary)}</table>
<h2>Edges in the directed graph</h2>
<p class="muted">From {EDGES}/directed_edges.csv (steps 3 to 5: research articles, order in {where}).
Delta and tool gap are positive here, counted from the tool cited first.</p>
<table><tr><th>Direction</th><th>Articles</th><th>Share</th><th>Median delta</th><th>Median tool gap</th>
<th>Σ 1/delta</th><th>Σ 1/tool gap</th></tr>{edge_rows}</table>
<h2>Distances in {where}</h2>
<p class="muted">Over the {len(deltas)} articles of the edges above, from directed_edges_raw.parquet. Positive (blue):
{a} cited first; negative (orange): {b} first.</p>
<h3>Delta <span class="muted">(references between them)</span></h3>{histogram(deltas, MAX_DELTA, 'delta')}
<h3>Tool gap <span class="muted">(tools between them)</span></h3>{histogram(gaps, MAX_GAP, 'tool gap')}
<p class="muted">In each article below, the strip shows the position of every bio.tools tool cited in {where}
(grey) and of {a} and {b}, highlighted in the text in the same colours.</p>
{''.join(body)}
</body></html>
"""
out = OUT_DIR / f'{a}__{b}.html'
out.write_text(page)
print(f'Written {out}')
