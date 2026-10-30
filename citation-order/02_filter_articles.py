"""Step 2: choose which citing articles go into the directed graph.

Shows how many articles there are of each type and status, keeps only the
well-parsed research articles (reviews cite by topic, not in order of use)
and writes them to kept_articles.parquet (one row per article), read by the
next steps.

Run from BH2026-InSoLiTo/:
    db-update/.venv/bin/python citation-order/02_filter_articles.py
"""

import duckdb

ARTICLES = 'db-update/raw_data/europepmc/export/articles.parquet'
OUTPUT = 'db-update/raw_data/citation-order/kept_articles.parquet'

con = duckdb.connect()

print('Articles by type and status:')
con.sql(f"""
    SELECT article_type, status, count(*) AS articles
    FROM '{ARTICLES}'
    GROUP BY article_type, status
    ORDER BY articles DESC
""").show(max_rows=100)

con.sql(f"""
    CREATE TEMP TABLE kept_articles AS
    SELECT pmcid, n_refs
    FROM '{ARTICLES}'
    WHERE status = 'ok' AND article_type = 'research-article'
""")

print('Articles kept (status ok, research articles):')
con.sql("SELECT count(*) AS articles FROM kept_articles").show()

con.sql(f"COPY kept_articles TO '{OUTPUT}' (FORMAT parquet)")
print(f'Written {OUTPUT}')
