"""Step 1b: look at the most cited works of the corpus, tool papers or not.

Shows the 12 most cited works and which bio.tools tool (if any) each one
matches, to see what the unmatched ones are. Read-only, writes nothing.
Needs tool_works.parquet from 01_match_tools.py.

Run from BH2026-InSoLiTo/:
    .venv/bin/python directed-graph/citation-order/01b_top_works.py
"""

import duckdb

WORKS = 'directed-graph/europepmc/data/export/works.parquet'
TOOL_WORKS = 'directed-graph/citation-order/data/tool_works.parquet'

con = duckdb.connect()

print('Most cited works in the corpus (tools = empty if no tool matches):')
con.sql(f"""
    SELECT w.work_id, w.n_citations, w.year, w.doi,
           string_agg(t.biotoolsID, ', ') AS tools,
           left(w.title, 50) AS title
    FROM '{WORKS}' w
    LEFT JOIN '{TOOL_WORKS}' t ON t.work_id = w.work_id
    WHERE w.work_id <= 12
    GROUP BY w.work_id, w.n_citations, w.year, w.doi, w.title
    ORDER BY w.work_id
""").show(max_width=250)
