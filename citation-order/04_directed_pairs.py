"""Step 4: directed pairs of tools in each article, with their distance.

Takes the order of the tools in each article (step 3) and makes one row per
pair and article: source is cited first, target later. Two distances:
  - delta: difference in `cited_rank_text` (counts every reference in
    between, tools or not)
  - tool_gap: the same counting only tool positions
Tools at the same position (a paper shared by several tools in bio.tools)
have no direction and give no pair between them. Writes the raw table to
directed_edges_raw.parquet. Needs tool_order.parquet from 03_order_tools.py.

Run from BH2026-InSoLiTo/:
    db-update/.venv/bin/python citation-order/04_directed_pairs.py
"""

import duckdb

TOOL_ORDER = 'db-update/raw_data/citation-order/tool_order.parquet'
OUTPUT = 'db-update/raw_data/citation-order/directed_edges_raw.parquet'

con = duckdb.connect()

# Position of each tool among the tools of its article (1, 2, 3...). Tools
# sharing a paper share the position, so they count as one step.
con.sql(f"""
    CREATE TEMP TABLE tool_order AS
    SELECT pmcid, biotoolsID, first_rank,
           dense_rank() OVER (PARTITION BY pmcid ORDER BY first_rank) AS tool_rank
    FROM '{TOOL_ORDER}'
""")

# Every pair of tools in the same article, the one cited first as source.
con.sql("""
    CREATE TEMP TABLE pairs AS
    SELECT a.pmcid, a.biotoolsID AS source, b.biotoolsID AS target,
           b.first_rank - a.first_rank AS delta,
           b.tool_rank - a.tool_rank AS tool_gap
    FROM tool_order a
    JOIN tool_order b ON b.pmcid = a.pmcid AND b.first_rank > a.first_rank
""")

print('Directed pairs:')
con.sql("""
    SELECT count(*) AS rows_pair_article,
           count(DISTINCT (source, target)) AS distinct_directed_pairs,
           count(DISTINCT pmcid) AS articles,
           median(delta) AS median_delta,
           median(tool_gap) AS median_tool_gap
    FROM pairs
""").show()

print('Example: pairs of PMC10000580 (maxquant 36, uniprot 37, complexheatmap 40, gsea = flexgsea 42 in step 3):')
con.sql("""
    SELECT source, target, delta, tool_gap
    FROM pairs
    WHERE pmcid = 'PMC10000580'
    ORDER BY delta, source, target
""").show()

con.sql(f"COPY (SELECT * FROM pairs ORDER BY pmcid, delta, source, target) TO '{OUTPUT}' (FORMAT parquet)")
print(f'Written {OUTPUT}')
