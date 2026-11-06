"""Step 5b: a smaller edge list of step 5 to look at in Cytoscape Desktop.

Keeps one arrow per pair, in its main direction (ties: alphabetical), and
only the strong, clear and close ones, so that the graph stays readable:
  - seen in at least MIN_ARTICLES articles counting both directions
  - share_forward of at least MIN_SHARE (clear direction)
  - median_delta of at most MAX_DELTA (cited close in the text)
Writes a CSV to import with File > Import > Network from File.

Needs the output of 05_sum_pairs.py. Run from BH2026-InSoLiTo/:
    db-update/.venv/bin/python citation-order/05b_cytoscape.py
"""

import duckdb

MIN_ARTICLES = 300
MIN_SHARE = 0.60
MAX_DELTA = 10

OUT_DIR = 'db-update/raw_data/citation-order'
EDGES = f'{OUT_DIR}/directed_edges.csv'
OUT_CSV = f'{OUT_DIR}/cytoscape_edges.csv'

con = duckdb.connect()

con.sql(f"""
    CREATE TEMP TABLE view_edges AS
    SELECT source, target,
           n_articles + n_articles_rev AS n_articles_total,
           n_articles, n_articles_rev,
           round(share_forward, 2) AS share_forward,
           round(sum_inv_delta, 2) AS sum_inv_delta,
           median_delta,
           round(sum_inv_tool_gap, 2) AS sum_inv_tool_gap,
           median_tool_gap
    FROM '{EDGES}'
    WHERE n_articles + n_articles_rev >= {MIN_ARTICLES}
      AND share_forward >= {MIN_SHARE}
      AND median_delta <= {MAX_DELTA}
""")

con.sql("""
    SELECT (SELECT count(*) FROM view_edges) AS edges,
           count(DISTINCT tool) AS tools
    FROM (SELECT source AS tool FROM view_edges
          UNION SELECT target FROM view_edges)
""").show()

con.sql(f"COPY (SELECT * FROM view_edges ORDER BY n_articles_total DESC) TO '{OUT_CSV}' (HEADER)")
print(f'Written {OUT_CSV}')
