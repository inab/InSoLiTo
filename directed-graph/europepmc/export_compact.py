"""Pack data/parsed/ into a compact, shareable set of single Parquet files.

The parsed ``references`` table repeats each cited paper's title, journal and IDs once
per citing paper (BLAST's title is stored thousands of times). This splits it into:

``works.parquet``      one row per *cited* paper (deduplicated by DOI, else PMID, else
                       PMCID), with how often it is cited across the corpus.
``citations.parquet``  one slim row per reference-list entry, pointing to ``work_id``.

``articles`` and ``mentions`` are copied over (mentions without the columns that can be
re-derived by a join). Everything is sorted and written with high zstd compression, and
a README.txt describing the tables is written alongside.

Uses DuckDB, so it runs in limited memory (spills to disk).

Example::

    python export_compact.py                      # -> data/export/
    python export_compact.py --keep-offsets       # also keep mentions.char_offset
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import duckdb

logger = logging.getLogger("export_compact")

README = """\
Co-citation corpus: proteomics + metabolomics open access papers (Europe PMC)
=============================================================================

Join keys
---------
  articles.pmcid  = citations.pmcid = mentions.pmcid      (the citing paper)
  citations (pmcid, ref_id) = mentions (pmcid, ref_id)    (one reference-list entry)
  citations.work_id = works.work_id                       (the cited paper)

articles.parquet: one row per citing paper
  pmcid, article_type, n_refs, n_refs_cited, n_mentions, n_unresolved_mentions,
  n_sections, status

works.parquet: one row per cited paper (deduplicated)
  work_id          integer id; 1 = most-cited work in the corpus
  doi, pmid, pmcid IDs of the cited paper (DOI lower-cased)
  title, source, year, first_author, publication_type
  n_citations      how many reference-list entries in the corpus point to this work

citations.parquet: one row per reference-list entry
  pmcid, ref_id    citing paper + the reference's XML id (B1, CR5, ...)
  ref_pos          position in the reference list
  work_id          -> works (empty if the reference has no DOI/PMID/PMCID)
  cited_rank       order of first citation in the body (1 = first), empty if never cited
  cited_rank_text  same, ignoring tables and figure captions: USE THIS as citation order
  citation_text    raw reference text, only for references with no PMID/DOI

mentions.parquet: one row per in-text citation, in reading order
  pmcid, mention_idx  citing paper + reading-order position (0 = first)
  ref_id              -> citations
  via                 xref | multi-rid | range (filled in from "1-4") | text-range
  sec_class           intro | methods | results | results_discussion | discussion |
                      conclusion | back | other | none
  sec_title           section heading, e.g. "2.3 Statistical analysis"
  sec_idx             top-level section number
  block_idx           paragraph / table cell (same value = same paragraph)
  block_type          p | td | th | title | ...
  sentence_idx        same value = same sentence
  in_table, in_caption

Quick start (Python)
--------------------
  import duckdb
  duckdb.sql('''
      SELECT m.pmcid, m.mention_idx, m.sec_class, m.sentence_idx, w.doi, w.title
      FROM 'mentions.parquet' m
      JOIN 'citations.parquet' c USING (pmcid, ref_id)
      JOIN 'works.parquet'     w USING (work_id)
      WHERE m.sec_class = 'methods'
      LIMIT 10
  ''').show()
"""

PARQUET_OPTS = "FORMAT parquet, COMPRESSION zstd, COMPRESSION_LEVEL 9, ROW_GROUP_SIZE 500000"


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).parent
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--parsed", type=Path, default=here / "data" / "parsed")
    p.add_argument("--out", type=Path, default=here / "data" / "export")
    p.add_argument("--keep-offsets", action="store_true",
                   help="Keep mentions.char_offset (finest-grained distance, about +80 MB).")
    p.add_argument("--memory-limit", default=None,
                   help="DuckDB memory limit, e.g. 4GB (default: DuckDB's own, 80%% of RAM).")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    args.out.mkdir(parents=True, exist_ok=True)
    tmp_dir = args.out / ".duckdb_tmp"
    con = duckdb.connect()
    if args.memory_limit:
        con.execute(f"SET memory_limit = '{args.memory_limit}'")
    con.execute(f"SET temp_directory = '{tmp_dir}'")
    con.execute("SET preserve_insertion_order = false")

    src = {t: str(args.parsed / t / "*.parquet") for t in ("articles", "references", "mentions")}
    out = {t: str(args.out / f"{t}.parquet") for t in ("articles", "works", "citations", "mentions")}

    def step(name: str, sql: str) -> None:
        t0 = time.time()
        con.execute(sql)
        logger.info("%-10s done in %.0f s", name, time.time() - t0)

    # Work key: DOI if present, else PMID, else PMCID. A view, so nothing is copied into memory.
    con.execute(f"""
        CREATE VIEW refs AS
        SELECT *, COALESCE(doi, 'pmid:' || pmid, 'pmc:' || pmcid_ref) AS wkey
        FROM read_parquet('{src['references']}')
    """)
    step("works_tbl", """
        CREATE TEMP TABLE works AS
        SELECT row_number() OVER (ORDER BY n_citations DESC, wkey) :: INTEGER AS work_id, *
        FROM (
            SELECT wkey,
                   any_value(doi)              AS doi,
                   any_value(pmid)             AS pmid,
                   any_value(pmcid_ref)        AS pmcid,
                   any_value(title)            AS title,
                   any_value(source)           AS source,
                   any_value(year)             AS year,
                   any_value(first_author)     AS first_author,
                   any_value(publication_type) AS publication_type,
                   count(*) :: INTEGER         AS n_citations
            FROM refs WHERE wkey IS NOT NULL GROUP BY wkey
        )
    """)
    step("articles", f"""
        COPY (SELECT * FROM read_parquet('{src['articles']}') ORDER BY pmcid)
        TO '{out['articles']}' ({PARQUET_OPTS})
    """)
    step("works", f"""
        COPY (SELECT * EXCLUDE (wkey) FROM works ORDER BY work_id)
        TO '{out['works']}' ({PARQUET_OPTS})
    """)
    step("citations", f"""
        COPY (
            SELECT r.pmcid, r.ref_id, r.ref_pos, w.work_id, r.cited_rank, r.cited_rank_text,
                   r.citation_text
            FROM refs r LEFT JOIN works w USING (wkey)
            ORDER BY r.pmcid, r.ref_pos
        ) TO '{out['citations']}' ({PARQUET_OPTS})
    """)
    offset_col = ", char_offset" if args.keep_offsets else ""
    step("mentions", f"""
        COPY (
            SELECT pmcid, mention_idx, ref_id, via, sec_class, sec_title, sec_idx, block_idx,
                   block_type, sentence_idx, in_table, in_caption{offset_col}
            FROM read_parquet('{src['mentions']}')
            ORDER BY pmcid, mention_idx
        ) TO '{out['mentions']}' ({PARQUET_OPTS})
    """)
    (args.out / "README.txt").write_text(README)

    total = 0
    for name, path in out.items():
        n = con.execute(f"SELECT count(*) FROM '{path}'").fetchone()[0]
        size = Path(path).stat().st_size
        total += size
        logger.info("%-16s %12s rows %8.0f MB", Path(path).name, f"{n:,}", size / 1e6)
    logger.info("Total %.0f MB -> %s", total / 1e6, args.out)
    con.close()
    for f in tmp_dir.glob("*"):
        f.unlink()
    if tmp_dir.exists():
        tmp_dir.rmdir()
    return 0


if __name__ == "__main__":
    sys.exit(main())
