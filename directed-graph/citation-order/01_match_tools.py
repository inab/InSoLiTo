"""Step 1: find which bio.tools papers appear among the works cited in the corpus.

Matches each bio.tools publication (Vedran's table) against Yojana's `works`
by DOI, PMID or PMCID. Prints counts and examples and writes the matches to
tool_works.parquet (one row per tool and paper), read by the next steps.

Run from BH2026-InSoLiTo/:
    .venv/bin/python directed-graph/citation-order/01_match_tools.py
"""

import duckdb

BIOTOOLS = 'directed-graph/biotools/data/biotools_publications.csv'
WORKS = 'directed-graph/europepmc/data/export/works.parquet'
OUTPUT = 'directed-graph/citation-order/data/tool_works.parquet'

con = duckdb.connect()

# One join per identifier: a single join with OR conditions forces DuckDB to
# compare every row with every row. UNION also removes the duplicates left
# when a paper matches by more than one identifier.
con.sql(f"""
    CREATE TEMP TABLE tool_works AS
    SELECT v.biotoolsID, w.work_id, w.title, w.n_citations
    FROM '{BIOTOOLS}' v
    JOIN '{WORKS}' w ON lower(v.doi) = w.doi
    UNION
    SELECT v.biotoolsID, w.work_id, w.title, w.n_citations
    FROM '{BIOTOOLS}' v
    JOIN '{WORKS}' w ON CAST(v.pmid AS VARCHAR) = CAST(w.pmid AS VARCHAR)
    UNION
    SELECT v.biotoolsID, w.work_id, w.title, w.n_citations
    FROM '{BIOTOOLS}' v
    JOIN '{WORKS}' w ON CAST(v.pmcid AS VARCHAR) = CAST(w.pmcid AS VARCHAR)
""")

print('Tools and papers found in the corpus:')
con.sql("""
    SELECT count(DISTINCT biotoolsID) AS tools, count(DISTINCT work_id) AS papers
    FROM tool_works
""").show()

print('Most cited tool papers:')
con.sql("""
    SELECT biotoolsID, work_id, n_citations, left(title, 60) AS title
    FROM tool_works
    ORDER BY n_citations DESC
    LIMIT 10
""").show()

con.sql(f"COPY tool_works TO '{OUTPUT}' (FORMAT parquet)")
print(f'Written {OUTPUT}')
