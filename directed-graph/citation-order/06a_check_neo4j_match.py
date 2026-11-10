"""
Step 6a: check how many tools and directed edges match the nodes in Neo4j.

Read-only. Nothing is written to Neo4j.

Goal: before loading CITED_BEFORE edges, know how many of the bio.tools IDs in
directed_edges.csv exist as `label` of a node in Neo4j, and therefore how many
edges could be loaded (both ends must exist).

Run from the repo root, with Neo4j up:
    .venv/bin/python directed-graph/citation-order/06a_check_neo4j_match.py
"""
import duckdb
from neo4j import GraphDatabase

EDGES_CSV = 'directed-graph/citation-order/data/directed_edges.csv'
NEO4J_URI = 'bolt://localhost:7687'

# 1. Distinct tool IDs in the directed edges
con = duckdb.connect()
con.execute(f"CREATE TABLE edges AS SELECT source, target FROM read_csv_auto('{EDGES_CSV}')")
ids = [r[0] for r in con.execute(
    "SELECT source FROM edges UNION SELECT target FROM edges").fetchall()]
print(f'Edges (rows) in CSV:        {con.execute("SELECT count(*) FROM edges").fetchone()[0]:,}')
print(f'Distinct tools in CSV:      {len(ids):,}')

# 2. Labels of Tool/Database nodes in Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=None)
with driver.session() as session:
    rows = session.run(
        'MATCH (n) WHERE n:Tool OR n:Database '
        'RETURN n.label AS label, labels(n)[0] AS type').data()
driver.close()

labels = [r['label'] for r in rows if r['label'] is not None]
print(f'Tool/Database nodes in Neo4j: {len(rows):,} ({len(rows) - len(labels)} without label)')
print(f'Sample of Neo4j labels:     {labels[:10]}')

# Labels that appear in more than one node (MERGE would not know which one to use)
con.execute('CREATE TABLE neo (label VARCHAR)')
con.executemany('INSERT INTO neo VALUES (?)', [(l,) for l in labels])
dup = con.execute(
    'SELECT label, count(*) n FROM neo GROUP BY label HAVING n > 1 ORDER BY n DESC').fetchall()
print(f'Labels repeated in Neo4j:   {len(dup):,} {dup[:5]}')

# 3. Matches: exact and ignoring case
con.execute('CREATE TABLE ids (id VARCHAR)')
con.executemany('INSERT INTO ids VALUES (?)', [(i,) for i in ids])
exact = con.execute(
    'SELECT count(*) FROM ids WHERE id IN (SELECT label FROM neo)').fetchone()[0]
nocase = con.execute(
    'SELECT count(*) FROM ids WHERE lower(id) IN (SELECT lower(label) FROM neo)').fetchone()[0]
print(f'Tools found in Neo4j:       {exact:,} exact, {nocase:,} ignoring case')

# 4. Edges with both ends in Neo4j (exact match)
both = con.execute(
    'SELECT count(*) FROM edges '
    'WHERE source IN (SELECT label FROM neo) AND target IN (SELECT label FROM neo)').fetchone()[0]
print(f'Edges with both ends found: {both:,}')

# Most frequent tools in the CSV that are NOT in Neo4j (to see what is missing)
missing = con.execute(
    'SELECT t, count(*) n FROM (SELECT source t FROM edges UNION ALL SELECT target FROM edges) '
    'WHERE t NOT IN (SELECT label FROM neo) GROUP BY t ORDER BY n DESC LIMIT 15').fetchall()
print('Top missing tools (tool, edges):')
for t, n in missing:
    print(f'  {t}: {n:,}')
