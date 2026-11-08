"""Step 3: order the tools cited in each article.

For every article kept in step 2, finds which entries of its reference list
are tool papers and when each tool is first cited. With SECTION set (e.g.
'methods'), the order comes from the mentions in that section only; with
SECTION = None, from the whole text (`cited_rank_text`). Shows how many
articles cite at least 2 tools, which are the ones that can give directed
pairs, and writes the order to tool_order.parquet (one row per article and
tool), overwriting the previous one.
Needs tool_works.parquet (step 1), kept_articles.parquet (step 2) and
mentions.parquet.

Run from BH2026-InSoLiTo/:
    .venv/bin/python directed-graph/citation-order/03_order_tools.py
"""

import duckdb

CITATIONS = 'directed-graph/europepmc/data/export/citations.parquet'
MENTIONS = 'directed-graph/europepmc/data/export/mentions.parquet'
TOOL_WORKS = 'directed-graph/citation-order/data/tool_works.parquet'
KEPT_ARTICLES = 'directed-graph/citation-order/data/kept_articles.parquet'
OUTPUT = 'directed-graph/citation-order/data/tool_order.parquet'

# Section used to order the references (a sec_class value of mentions, e.g.
# 'methods'). None = the whole text, with cited_rank_text as before.
SECTION = 'methods'

con = duckdb.connect()

# Position of each reference in each kept article (1 = cited first).
if SECTION is None:
    # Whole text: first citation in the body, ignoring tables and figure
    # captions. References never cited in the text are left out.
    con.sql(f"""
        CREATE TEMP TABLE ref_rank AS
        SELECT c.pmcid, c.ref_id, c.cited_rank_text AS ref_rank
        FROM '{CITATIONS}' c
        JOIN '{KEPT_ARTICLES}' a ON a.pmcid = c.pmcid
        WHERE c.cited_rank_text IS NOT NULL
    """)
else:
    # Only SECTION: first mention of each reference there (tables and figure
    # captions left out), then numbered 1, 2, 3... in that order, so that
    # delta in step 4 still counts references, not repeated mentions.
    con.execute(f"""
        CREATE TEMP TABLE ref_rank AS
        WITH first_mention AS (
            SELECT m.pmcid, m.ref_id, min(m.mention_idx) AS first_idx
            FROM '{MENTIONS}' m
            JOIN '{KEPT_ARTICLES}' a ON a.pmcid = m.pmcid
            WHERE m.sec_class = ?
              AND m.in_table IS NOT TRUE
              AND m.in_caption IS NOT TRUE
            GROUP BY m.pmcid, m.ref_id
        )
        SELECT pmcid, ref_id,
               dense_rank() OVER (PARTITION BY pmcid ORDER BY first_idx) AS ref_rank
        FROM first_mention
    """, [SECTION])
print(f'Section used for the order: {SECTION or "whole text"}')

# One row per article and tool. A tool with several papers in the same
# article keeps the one cited first. References with no position (not cited
# in the text, or not in SECTION) are not in ref_rank and are left out.
con.sql(f"""
    CREATE TEMP TABLE tool_order AS
    SELECT c.pmcid, t.biotoolsID, min(r.ref_rank) AS first_rank
    FROM '{CITATIONS}' c
    JOIN ref_rank r ON r.pmcid = c.pmcid AND r.ref_id = c.ref_id
    JOIN '{TOOL_WORKS}' t ON t.work_id = c.work_id
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
