"""
Step 6: load the directed edges into Neo4j as CITED_BEFORE relationships.

Goal: show the directed edges in InSoLiTo next to the co-citation edges
(METAOCCUR), without touching anything else in the database.

- One relationship per row of directed_edges.csv: both directions of a pair are
  loaded as they are, each with its own numbers.
- Tools are matched to existing Tool/Database nodes by `label` (bio.tools ID),
  ignoring case. No data is changed: only the lookup ignores case.
- Rows whose source or target is not in Neo4j are skipped (and counted).
- Only MERGE: nodes are never created or deleted. Re-running updates the
  numbers of edges already loaded (it does not remove edges that are no longer
  in the CSV).
- Only against localhost.

With DRY_RUN = True it only prints what it would load and writes nothing.

Run from the repo root, with Neo4j up:
    .venv/bin/python directed-graph/citation-order/06_load_neo4j.py
"""
import duckdb
from neo4j import GraphDatabase

EDGES_CSV = 'directed-graph/citation-order/data/directed_edges.csv'
NEO4J_URI = 'bolt://localhost:7687'
DRY_RUN = True
BATCH_SIZE = 10_000

# Columns stored on each relationship (the *_rev columns are not stored: the
# reverse direction is its own relationship with its own numbers)
PROPS = ['n_articles', 'sum_inv_delta', 'median_delta',
         'sum_inv_tool_gap', 'median_tool_gap', 'share_forward']

if 'localhost' not in NEO4J_URI and '127.0.0.1' not in NEO4J_URI:
    raise SystemExit(f'Refusing to write to a non-local Neo4j: {NEO4J_URI}')

driver = GraphDatabase.driver(NEO4J_URI, auth=None)

# 1. Lookup table: lowercase label -> Neo4j node id
with driver.session() as session:
    nodes = session.run(
        'MATCH (n) WHERE n:Tool OR n:Database RETURN id(n) AS id, n.label AS label').data()

by_lower = {}
for n in nodes:
    by_lower.setdefault(n['label'].lower(), []).append(n)

# Labels that only differ in case would point to two nodes: leave them out
clashes = {k: [n['label'] for n in v] for k, v in by_lower.items() if len(v) > 1}
print(f'Tool/Database nodes:         {len(nodes):,}')
print(f'Labels clashing by case:     {len(clashes):,} {list(clashes.values())[:5]}')
node_id = {k: v[0]['id'] for k, v in by_lower.items() if len(v) == 1}

# 2. Read the edges and map both ends to node ids
con = duckdb.connect()
rows = con.execute(
    f"SELECT source, target, {', '.join(PROPS)} FROM read_csv_auto('{EDGES_CSV}')").fetchall()
print(f'Rows in CSV:                 {len(rows):,}')

batch_rows, seen = [], set()
missing = self_loops = duplicates = 0
for source, target, *values in rows:
    a, b = node_id.get(source.lower()), node_id.get(target.lower())
    if a is None or b is None:
        missing += 1
        continue
    if a == b:              # two CSV IDs that land on the same node
        self_loops += 1
        continue
    if (a, b) in seen:      # same node pair reached from differently-cased IDs
        duplicates += 1
        continue
    seen.add((a, b))
    batch_rows.append({'a': a, 'b': b, 'props': dict(zip(PROPS, values))})

print(f'Skipped, tool not in Neo4j:  {missing:,}')
print(f'Skipped, same node:          {self_loops:,}')
print(f'Skipped, repeated pair:      {duplicates:,}')
print(f'Edges to load:               {len(batch_rows):,}')

# 3. Load in batches
if DRY_RUN:
    print('DRY_RUN = True: nothing written.')
else:
    query = (
        'UNWIND $rows AS row '
        'MATCH (a) WHERE id(a) = row.a '
        'MATCH (b) WHERE id(b) = row.b '
        'MERGE (a)-[r:CITED_BEFORE]->(b) '
        'SET r += row.props')
    with driver.session() as session:
        for i in range(0, len(batch_rows), BATCH_SIZE):
            session.run(query, rows=batch_rows[i:i + BATCH_SIZE]).consume()
            print(f'  loaded {min(i + BATCH_SIZE, len(batch_rows)):,} / {len(batch_rows):,}')
        total = session.run(
            'MATCH ()-[r:CITED_BEFORE]->() RETURN count(r) AS n').single()['n']
    print(f'CITED_BEFORE relationships in Neo4j: {total:,}')

driver.close()
