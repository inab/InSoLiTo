"""Parse downloaded Europe PMC JATS XML into citation tables for co-citation analysis.

For every article this extracts three tables, written as Parquet shards:

``articles``    one row per paper: article type, counts, parse status.
``references``  one row per reference-list entry: IDs (PMID / PMCID / DOI), title,
                year, position in the reference list, and *cited_rank* - the order
                in which the reference is first cited in the body text.
``mentions``    one row per in-text citation of a reference, in reading order, with
                where it occurs: section class (intro / methods / results / ...),
                section title, paragraph (block) index, sentence index, and whether
                it is in a table or caption.

Citation order is taken from the in-text ``<xref ref-type="bibr">`` tags, *not* from
the reference-list order, so it is correct for numbered, author-year and hybrid
citation styles alike. Citation ranges such as "[3-7]" are expanded to include the
references in between.

Work is split into shards of N files; finished shards are skipped, so the run can be
stopped and restarted.

Example::

    python parse_jats.py --workers 8
    python parse_jats.py --limit 2000 --out data/parsed_test   # quick test
"""

from __future__ import annotations

import argparse
import bisect
import gzip
import logging
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qs

import pyarrow as pa
import pyarrow.parquet as pq
from lxml import etree

logger = logging.getLogger("parse_jats")

# --------------------------------------------------------------------------- #
# Section classification
# --------------------------------------------------------------------------- #

# Order matters: first match wins. Applied to sec-type and to the section title.
SECTION_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("back", re.compile(
        r"acknowledg|funding|author.?s?.? contribution|contributor|conflicts? of interest|"
        r"competing interest|declaration|data availability|availability of data|code availability|"
        r"supplementa|abbreviation|glossary|ethic|consent|footnote|disclosure|"
        r"associated data|ref-list|^references?$|bibliography|fn-group|"
        r"publisher.?s note|additional information|electronic supplementary")),
    ("results_discussion", re.compile(r"results?\s*(and|&)\s*discussion")),
    ("intro", re.compile(r"^intro|introduction|background")),
    ("methods", re.compile(
        r"method|material|experimental|procedure|study design|patients|participants|"
        r"subjects|samples? (preparation|collection)|data (collection|analysis|acquisition)|"
        r"statistic")),
    ("results", re.compile(r"^results?|findings")),
    ("discussion", re.compile(r"discussion")),
    ("conclusion", re.compile(r"conclu|summary|outlook|perspective|future direction")),
]

# Leading section numbers: "1.", "2.3 ", "IV.", "ii)" - Roman numerals only with . or ).
_NUMBERING = re.compile(r"^\s*(?:\d+(?:\.\d+)*\.?|[ivxlc]+[.)])\s*")


def classify_section(sec_type: str | None, title: str | None) -> str:
    for text in (sec_type, title):
        if not text:
            continue
        t = _NUMBERING.sub("", text.strip().lower())
        for name, pat in SECTION_PATTERNS:
            if pat.search(t):
                return name
    return "other"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

BLOCK_TAGS = {"p", "td", "th", "title", "caption", "label", "list-item", "disp-quote", "def"}
SKIP_TAGS = {"ref-list", "fn-group", "ack", "glossary", "app-group", "back", "math",
             "inline-formula", "disp-formula", "tex-math", "graphic", "media", "object-id"}
TABLE_TAGS = {"table-wrap", "table"}
CAPTION_TAGS = {"caption", "fig"}
DASH_ONLY = re.compile(r"^\s*[‐-―\-−~]\s*$")
TEXT_RANGE = re.compile(r"^\s*\[?\(?(\d+)\s*[‐-―\-−]\s*(\d+)\)?\]?\s*$")
# Sentence end: . ! ? followed by space(s) and an uppercase letter / digit / opening bracket.
# Deliberately simple; "et al. Smith" style false splits are rare inside one paragraph.
SENTENCE_END = re.compile(r"(?<!\bet al)(?<!\bFig)(?<!\bref)(?<!\be\.g)(?<!\bi\.e)[.!?]\s+(?=[A-Z0-9\[(])")
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>]+", re.I)
MAX_RANGE_GAP = 50


def localname(el) -> str | None:
    tag = el.tag
    if not isinstance(tag, str):  # comments, processing instructions
        return None
    return tag.rsplit("}", 1)[-1]


def norm_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    doi = doi.strip().lower()
    doi = re.sub(r"^(https?://)?(dx\.)?doi\.org/|^doi:\s*", "", doi)
    doi = doi.rstrip(".,;)")
    return doi or None


def text_of(el) -> str:
    return " ".join("".join(el.itertext()).split()) if el is not None else ""


# --------------------------------------------------------------------------- #
# Reference list
# --------------------------------------------------------------------------- #


XLINK_HREF = "{http://www.w3.org/1999/xlink}href"
ID_KINDS = ("pmid", "pmcid", "doi")
YEAR_RE = re.compile(r"\b(1[89]\d{2}|20\d{2})\b")


def _scholar_params(ref) -> dict[str, list[str]]:
    """Query params of Europe PMC's google-scholar ext-link (title, author, year, ids)."""
    for ext in ref.iter("ext-link"):
        if (ext.get("ext-link-type") or "").lower() == "google-scholar":
            return parse_qs(ext.get(XLINK_HREF) or "")
    return {}


def parse_references(root) -> list[dict]:
    """All <ref> elements in document order (reference list may be in body or back).

    Europe PMC writes references in two ways: structured (<element-citation> with
    <pub-id>, <article-title>, <year>) or a free-text citation string plus typed
    <ext-link>s (pmid / pmcid / doi / google-scholar). Fields are filled from the
    first source that has them: pub-id > typed ext-link > google-scholar link > text.
    """
    refs = []
    for pos, ref in enumerate(root.iter("ref"), 1):
        ids: dict[str, str] = {}
        for pid in ref.iter("pub-id"):
            kind = (pid.get("pub-id-type") or "").lower()
            val = (pid.text or "").strip()
            if kind in ID_KINDS and val:
                ids.setdefault(kind, val)
        for ext in ref.iter("ext-link"):
            kind = (ext.get("ext-link-type") or "").lower()
            val = (ext.get(XLINK_HREF) or ext.text or "").strip()
            if kind in ID_KINDS and val:
                ids.setdefault(kind, val)
        scholar = _scholar_params(ref)
        for kind in ID_KINDS:
            if kind not in ids and scholar.get(kind):
                ids[kind] = scholar[kind][0]
        citation_text = text_of(ref.find(".//named-content[@content-type='citation-string']")) \
            or text_of(ref)
        if "doi" not in ids:
            for ext in ref.iter("ext-link", "uri"):
                m = DOI_RE.search(ext.get(XLINK_HREF) or ext.text or "")
                if m:
                    ids["doi"] = m.group(0)
                    break
        if "doi" not in ids:
            m = DOI_RE.search(citation_text)
            if m:
                ids["doi"] = m.group(0)

        # A ref can hold several citation variants (citation-alternatives): use the first.
        cits = list(ref.iter("element-citation", "mixed-citation", "nlm-citation", "citation"))
        cit = cits[0] if cits else ref
        surname = cit.find(".//name/surname")
        if surname is None:
            surname = cit.find(".//string-name/surname")
        first_author = ((surname.text or "").strip() or None) if surname is not None else None
        if not first_author and scholar.get("author"):
            first_author = scholar["author"][0].split()[-1]  # "K. Adamberg" -> "Adamberg"

        year = YEAR_RE.search(cit.findtext(".//year") or "")
        year = year.group(0) if year else (scholar.get("publication_year") or [None])[0]
        if not year:
            m = YEAR_RE.search(citation_text)
            year = m.group(0) if m else None

        pmid = re.sub(r"\D", "", ids.get("pmid", "")) or None
        pmcid = re.sub(r"\D", "", ids.get("pmcid", "")) or None
        refs.append({
            "ref_id": ref.get("id") or f"__pos{pos}",
            "ref_pos": pos,
            "label": (ref.findtext("label") or "").strip() or None,
            "pmid": pmid,
            "pmcid_ref": f"PMC{pmcid}" if pmcid else None,
            "doi": norm_doi(ids.get("doi")),
            "title": text_of(cit.find(".//article-title")) or (scholar.get("title") or [None])[0],
            "source": text_of(cit.find(".//source")) or (scholar.get("journal") or [None])[0],
            "year": year,
            "first_author": first_author,
            "publication_type": cit.get("publication-type") or cit.get("citation-type"),
            # Raw text only where there is no PMID/DOI to match on (keeps the table small).
            "citation_text": (citation_text[:1000] or None) if not (pmid or ids.get("doi")) else None,
        })
    return refs


# --------------------------------------------------------------------------- #
# Body walk
# --------------------------------------------------------------------------- #


@dataclass
class Ctx:
    sec_class: str = "none"   # class of the top-level section
    sec_title: str | None = None  # innermost section title
    sec_idx: int = -1         # index of the top-level section
    block: int = -1
    block_type: str | None = None
    in_table: bool = False
    in_caption: bool = False


@dataclass
class Walker:
    ref_pos: dict[str, int]          # ref_id -> position in reference list
    pos_ref: dict[int, str]          # position -> ref_id
    range_extra: dict  # start xref element -> intermediate ref ids
    buf: list[str] = field(default_factory=list)
    offset: int = 0
    boundaries: list[int] = field(default_factory=list)  # forced sentence breaks
    mentions: list[dict] = field(default_factory=list)
    n_blocks: int = 0
    n_top_secs: int = 0

    def emit_text(self, s: str | None) -> None:
        if s:
            self.buf.append(s)
            self.offset += len(s)

    def add_mention(self, rid: str, ctx: Ctx, via: str) -> None:
        self.mentions.append({
            "ref_id": rid, "offset": self.offset, "via": via,
            "sec_class": ctx.sec_class, "sec_title": ctx.sec_title, "sec_idx": ctx.sec_idx,
            "block_idx": ctx.block, "block_type": ctx.block_type,
            "in_table": ctx.in_table, "in_caption": ctx.in_caption,
        })

    def walk(self, el, ctx: Ctx, depth: int = 0) -> None:
        name = localname(el)
        if name is None or name in SKIP_TAGS:
            return
        if name == "sec":
            sec_type = el.get("sec-type")
            title = text_of(el.find("title")) or None
            if sec_type == "ref-list" or el.find("ref-list") is not None and len(el) <= 2:
                return
            if depth_is_top(el):
                self.n_top_secs += 1
                ctx = Ctx(classify_section(sec_type, title), title, self.n_top_secs - 1,
                          ctx.block, ctx.block_type, ctx.in_table, ctx.in_caption)
            else:
                ctx = Ctx(ctx.sec_class, title or ctx.sec_title, ctx.sec_idx,
                          ctx.block, ctx.block_type, ctx.in_table, ctx.in_caption)
        if name in TABLE_TAGS and not ctx.in_table:
            ctx = Ctx(**{**ctx.__dict__, "in_table": True})
        if name in CAPTION_TAGS and not ctx.in_caption:
            ctx = Ctx(**{**ctx.__dict__, "in_caption": True})
        is_block = name in BLOCK_TAGS
        if is_block:
            self.n_blocks += 1
            self.boundaries.append(self.offset)
            ctx = Ctx(**{**ctx.__dict__, "block": self.n_blocks - 1, "block_type": name})

        if name == "xref" and el.get("ref-type") == "bibr":
            rids = (el.get("rid") or "").split()
            via = "multi-rid" if len(rids) > 1 else "xref"
            for rid in rids:
                self.add_mention(rid, ctx, via)
            # "<xref rid='B3'>3-7</xref>": range spelled inside one tag
            m = TEXT_RANGE.match(text_of(el))
            if len(rids) == 1 and m and rids[0] in self.ref_pos:
                start = self.ref_pos[rids[0]]
                gap = int(m.group(2)) - int(m.group(1))
                if 0 < gap <= MAX_RANGE_GAP:
                    for p in range(start + 1, start + gap + 1):
                        if p in self.pos_ref:
                            self.add_mention(self.pos_ref[p], ctx, "text-range")
            for rid in self.range_extra.get(el, ()):
                self.add_mention(rid, ctx, "range")

        self.emit_text(el.text)
        for child in el:
            self.walk(child, ctx, depth + 1)
            if localname(child) in BLOCK_TAGS and is_block:
                self.boundaries.append(self.offset)  # text after a nested block = new sentence
            self.emit_text(child.tail)


def depth_is_top(sec) -> bool:
    """True if no ancestor is a <sec> (i.e. a top-level section of the body)."""
    parent = sec.getparent()
    while parent is not None:
        if localname(parent) == "sec":
            return False
        if localname(parent) == "body":
            return True
        parent = parent.getparent()
    return True


def _bibr_target(node):
    """The single bibr xref represented by node (itself, or a wrapper like <sup>)."""
    if localname(node) == "xref" and node.get("ref-type") == "bibr":
        return node
    if localname(node) in ("sup", "bold", "italic") and len(node) == 1 and not (node.text or "").strip():
        child = node[0]
        if localname(child) == "xref" and child.get("ref-type") == "bibr" and not (child.tail or "").strip():
            return child
    return None


def find_ranges(body, ref_pos: dict[str, int], pos_ref: dict[int, str]) -> dict:
    """Map start-xref element -> refs strictly between start and end of an "a–b" range.

    Keyed on the element object, not id(): lxml creates proxy objects on access, so
    id() is not stable - but the same proxy is reused while this dict holds it.
    """
    extra: dict = {}
    for parent in body.iter():
        if localname(parent) is None or len(parent) < 2:
            continue
        children = list(parent)
        for a, b in zip(children, children[1:]):
            if not DASH_ONLY.match(a.tail or ""):
                continue
            xa, xb = _bibr_target(a), _bibr_target(b)
            if xa is None or xb is None:
                continue
            ra, rb = (xa.get("rid") or "").split(), (xb.get("rid") or "").split()
            if not ra or not rb:
                continue
            pa_, pb_ = ref_pos.get(ra[-1]), ref_pos.get(rb[0])
            if pa_ is None or pb_ is None or not 1 < pb_ - pa_ <= MAX_RANGE_GAP:
                continue
            extra[xa] = [pos_ref[p] for p in range(pa_ + 1, pb_) if p in pos_ref]
    return extra


# --------------------------------------------------------------------------- #
# Per-file parse
# --------------------------------------------------------------------------- #


def parse_file(path: Path) -> tuple[dict, list[dict], list[dict]]:
    pmcid = path.name.split(".")[0]
    article = {"pmcid": pmcid, "article_type": None, "n_refs": 0, "n_refs_cited": 0,
               "n_mentions": 0, "n_unresolved_mentions": 0, "n_sections": 0, "status": "ok"}
    try:
        with gzip.open(path, "rb") as fh:
            root = etree.fromstring(fh.read(), parser=etree.XMLParser(recover=True, huge_tree=True))
    except Exception as exc:  # noqa: BLE001 - record and move on
        article["status"] = f"error: {type(exc).__name__}"
        return article, [], []
    if root is None:
        article["status"] = "error: empty"
        return article, [], []

    article["article_type"] = root.get("article-type")
    refs = parse_references(root)
    article["n_refs"] = len(refs)
    body = root.find(".//body")
    if body is None:
        article["status"] = "no_body"
        return article, _finish_refs(pmcid, refs, {}, {}), []

    ref_pos = {r["ref_id"]: r["ref_pos"] for r in refs}
    pos_ref = {r["ref_pos"]: r["ref_id"] for r in refs}
    walker = Walker(ref_pos, pos_ref, find_ranges(body, ref_pos, pos_ref))
    walker.walk(body, Ctx())
    article["n_sections"] = walker.n_top_secs

    # Sentence index = number of sentence breaks (punctuation or block start) before offset.
    text = "".join(walker.buf)
    breaks = sorted(set(walker.boundaries) | {m.end() for m in SENTENCE_END.finditer(text)})

    mentions = []
    first_mention: dict[str, int] = {}
    first_text_mention: dict[str, int] = {}  # running text only (no tables / captions)
    n_unresolved = 0
    for i, m in enumerate(walker.mentions):
        if m["ref_id"] not in ref_pos:
            n_unresolved += 1
        first_mention.setdefault(m["ref_id"], i)
        if not (m["in_table"] or m["in_caption"]):
            first_text_mention.setdefault(m["ref_id"], i)
        mentions.append({
            "pmcid": pmcid,
            "mention_idx": i,
            "ref_id": m["ref_id"],
            "ref_pos": ref_pos.get(m["ref_id"]),
            "via": m["via"],
            "sec_class": m["sec_class"],
            "sec_title": m["sec_title"],
            "sec_idx": m["sec_idx"],
            "block_idx": m["block_idx"],
            "block_type": m["block_type"],
            "sentence_idx": bisect.bisect_right(breaks, m["offset"]),
            "char_offset": m["offset"],
            "in_table": m["in_table"],
            "in_caption": m["in_caption"],
        })
    article["n_mentions"] = len(mentions)
    article["n_unresolved_mentions"] = n_unresolved
    refs_out = _finish_refs(pmcid, refs, first_mention, first_text_mention)
    article["n_refs_cited"] = sum(1 for r in refs_out if r["cited_rank"] is not None)
    return article, refs_out, mentions


def _rank(first: dict[str, int]) -> dict[str, int]:
    """ref_id -> 1-based rank by first appearance."""
    return {rid: r for r, (_, rid) in enumerate(sorted((i, rid) for rid, i in first.items()), 1)}


def _finish_refs(
    pmcid: str, refs: list[dict], first_mention: dict[str, int], first_text_mention: dict[str, int]
) -> list[dict]:
    """Add citation-order ranks.

    cited_rank       1 = first reference cited anywhere in the body.
    cited_rank_text  same, counting running text only - tables and figure captions are
                     often placed out of reading order in JATS, so this is the cleaner order.
    """
    rank, rank_text = _rank(first_mention), _rank(first_text_mention)
    return [{
        "pmcid": pmcid, **r,
        "cited_rank": rank.get(r["ref_id"]),
        "cited_rank_text": rank_text.get(r["ref_id"]),
        "first_mention_idx": first_mention.get(r["ref_id"]),
    } for r in refs]


# --------------------------------------------------------------------------- #
# Sharded driver
# --------------------------------------------------------------------------- #

SCHEMAS = {
    "articles": pa.schema([
        ("pmcid", pa.string()), ("article_type", pa.string()), ("n_refs", pa.int32()),
        ("n_refs_cited", pa.int32()), ("n_mentions", pa.int32()),
        ("n_unresolved_mentions", pa.int32()), ("n_sections", pa.int32()), ("status", pa.string()),
    ]),
    "references": pa.schema([
        ("pmcid", pa.string()), ("ref_id", pa.string()), ("ref_pos", pa.int32()),
        ("label", pa.string()), ("pmid", pa.string()), ("pmcid_ref", pa.string()),
        ("doi", pa.string()), ("title", pa.string()), ("source", pa.string()),
        ("year", pa.string()), ("first_author", pa.string()), ("publication_type", pa.string()),
        ("citation_text", pa.string()), ("cited_rank", pa.int32()), ("cited_rank_text", pa.int32()), ("first_mention_idx", pa.int32()),
    ]),
    "mentions": pa.schema([
        ("pmcid", pa.string()), ("mention_idx", pa.int32()), ("ref_id", pa.string()),
        ("ref_pos", pa.int32()), ("via", pa.string()), ("sec_class", pa.string()),
        ("sec_title", pa.string()), ("sec_idx", pa.int32()), ("block_idx", pa.int32()),
        ("block_type", pa.string()), ("sentence_idx", pa.int32()), ("char_offset", pa.int32()),
        ("in_table", pa.bool_()), ("in_caption", pa.bool_()),
    ]),
}


def parse_shard(shard_idx: int, files: list[str], out_dir: str) -> dict[str, int]:
    tables: dict[str, list[dict]] = {k: [] for k in SCHEMAS}
    for f in files:
        art, refs, ments = parse_file(Path(f))
        tables["articles"].append(art)
        tables["references"].extend(refs)
        tables["mentions"].extend(ments)
    counts = {}
    for name, rows in tables.items():
        dest = Path(out_dir) / name / f"part-{shard_idx:05d}.parquet"
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".parquet.part")
        pq.write_table(pa.Table.from_pylist(rows, schema=SCHEMAS[name]), tmp, compression="zstd")
        tmp.replace(dest)
        counts[name] = len(rows)
    return counts


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    here = Path(__file__).parent
    p.add_argument("--xml-dir", type=Path, default=here / "data" / "xml")
    p.add_argument("--out", type=Path, default=here / "data" / "parsed")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--shard-size", type=int, default=2000)
    p.add_argument("--limit", type=int, default=None, help="Only parse the first N files (testing).")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    files = sorted(str(f) for f in args.xml_dir.glob("*/*.xml.gz"))
    if args.limit:
        files = files[: args.limit]
    shards = [files[i:i + args.shard_size] for i in range(0, len(files), args.shard_size)]
    # A shard is done only when all three tables exist (written last-to-first is not guaranteed).
    todo = [i for i in range(len(shards))
            if not all((args.out / t / f"part-{i:05d}.parquet").exists() for t in SCHEMAS)]
    logger.info("%d files in %d shards; %d shards to parse with %d workers",
                len(files), len(shards), len(todo), args.workers)

    totals: dict[str, int] = {}
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(parse_shard, i, shards[i], str(args.out)): i for i in todo}
        for n, fut in enumerate(as_completed(futs), 1):
            for k, v in fut.result().items():
                totals[k] = totals.get(k, 0) + v
            el = time.time() - t0
            logger.info("shard %d/%d done  %s  (%.0f s elapsed, ETA %.0f min)",
                        n, len(todo), totals, el, el / n * (len(todo) - n) / 60)
    logger.info("Finished -> %s", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
