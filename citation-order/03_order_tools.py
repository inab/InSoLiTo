"""Step 3: order the tools cited in each article.

For every article kept in step 2, finds which entries of its reference list
are tool papers and when each tool is first cited in the text
(`cited_rank_text`). Shows how many articles cite at least 2 tools, which are
the ones that can give directed pairs, and writes the order to
tool_order.parquet (one row per article and tool).
Needs tool_works.parquet (step 1) and kept_articles.parquet (step 2).

Run from BH2026-InSoLiTo/:
    db-update/.venv/bin/python citation-order/03_order_tools.py
"""

import duckdb

CITATIONS = 'db-update/raw_data/europepmc/export/citations.parquet'
TOOL_WORKS = 'db-update/raw_data/citation-order/tool_works.parquet'
KEPT_ARTICLES = 'db-update/raw_data/citation-order/kept_articles.parquet'
OUTPUT = 'db-update/raw_data/citation-order/tool_order.parquet'

con = duckdb.connect()

# One row per article and tool. A tool with several papers in the same
# article keeps the one cited first. References never cited in the text
# (empty cited_rank_text) cannot be ordered and are left out.
con.sql(f"""
    CREATE TEMP TABLE tool_order AS
    SELECT c.pmcid, t.biotoolsID, min(c.cited_rank_text) AS first_rank
    FROM '{CITATIONS}' c
    JOIN '{KEPT_ARTICLES}' a ON a.pmcid = c.pmcid
    JOIN '{TOOL_WORKS}' t ON t.work_id = c.work_id
    WHERE c.cited_rank_text IS NOT NULL
    GROUP BY c.pmcid, t.biotoolsID
""")

print('Articles by number of tools cited:')
con.sql("""
    WITH per_article AS (
        SELECT pmcid, count(*) AS n_tools
        FROM tool_order
        GROUP BY pmcid
    )
    SELECT count(*) AS with_tools,
           count(*) FILTER (WHERE n_tools >= 2) AS with_2plus_tools,
           median(n_tools) AS median_tools,
           max(n_tools) AS max_tools
    FROM per_article
""").show()

print('Example: an article citing MaxQuant and 3 to 8 tools, in citation order:')
con.sql("""
    SELECT pmcid, biotoolsID, first_rank
    FROM tool_order
    WHERE pmcid = (
        SELECT pmcid
        FROM tool_order
        GROUP BY pmcid
        HAVING bool_or(biotoolsID = 'maxquant') AND count(*) BETWEEN 3 AND 8
        ORDER BY pmcid
        LIMIT 1
    )
    ORDER BY first_rank
""").show()

# A paper shared by several tools puts all of them at the same position,
# which would give pairs with no direction (delta 0).
print('Positions shared by several tools (same paper, several tools):')
con.sql("""
    SELECT count(*) AS shared_positions
    FROM (
        SELECT pmcid, first_rank
        FROM tool_order
        GROUP BY pmcid, first_rank
        HAVING count(*) > 1
    )
""").show()

con.sql(f"COPY (SELECT * FROM tool_order ORDER BY pmcid, first_rank) TO '{OUTPUT}' (FORMAT parquet)")
print(f'Written {OUTPUT}')
