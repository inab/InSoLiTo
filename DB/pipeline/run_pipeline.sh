#!/usr/bin/env bash
# Full InSoLiTo DB rebuild: PubMed baseline + OEB snapshot -> SQLite -> CSV -> local Neo4j -> JSON.
# Run from the repo root:  nohup DB/pipeline/run_pipeline.sh > DB/raw_data/pipeline.log 2>&1 &
# REUSE_PUBLICATIONS=1 DB/pipeline/run_pipeline.sh ... reuses the Publications table of an existing $DB_NAME.db
# The Neo4j step deletes the whole DB it points to (DB/pipeline/neo4j/full-config.ini): local compose only.
set -euo pipefail

DB_NAME=DB/raw_data/insolito_2026
PUBMED_DIR=DB/raw_data/pubmed_baseline
OEB_JSON=DB/raw_data/oeb_tools.json
IMPORT_DIR=DB/InSoLiToImport
NEO4J_CONFIG=DB/pipeline/neo4j/full-config.ini
PYTHON=.venv/bin/python
REUSE_PUBLICATIONS=${REUSE_PUBLICATIONS:-0}

step() { echo; echo "=== [$(date '+%F %T')] $* ==="; }

cd "$(dirname "$0")/../.."

# Checks before hours of work
if [ "$REUSE_PUBLICATIONS" = 1 ]; then
    [ -e "$DB_NAME.db" ] || { echo "REUSE_PUBLICATIONS=1 but $DB_NAME.db does not exist"; exit 1; }
    REUSE_FLAG=--reuse-publications
else
    [ -e "$DB_NAME.db" ] && { echo "$DB_NAME.db already exists, move or delete it first"; exit 1; }
    REUSE_FLAG=
fi
[ -w "$IMPORT_DIR" ] || { echo "$IMPORT_DIR is not writable (Neo4j chown?), fix permissions first"; exit 1; }
if docker compose -f docker-compose.yml ps --status running --services | grep -q '^InSoLiToDatabase2$'; then
    echo "Neo4j is running: stop it (docker compose down) before exporting the CSVs"; exit 1
fi

step "1/4 SQLite: CreateDatabase.py"
$PYTHON -u DB/pipeline/CreateDatabase.py "$DB_NAME" "$PUBMED_DIR" "$OEB_JSON" $REUSE_FLAG

step "2/4 CSV: export_csv.py"
$PYTHON -u DB/pipeline/export_csv.py "$DB_NAME.db" "$IMPORT_DIR"

step "3/4 Start local Neo4j"
docker compose -f docker-compose.yml up -d InSoLiToDatabase2
HTTP_PORT=$(grep -E '^NEO4J_HTTP_PORT=' .env | cut -d= -f2)
for _ in $(seq 60); do
    curl -sf "http://localhost:${HTTP_PORT:-7474}" > /dev/null && break
    sleep 5
done
curl -sf "http://localhost:${HTTP_PORT:-7474}" > /dev/null || { echo "Neo4j did not answer after 5 min"; exit 1; }

step "4/4 Neo4j import: CreateNeo4jDataset.py"
$PYTHON -u DB/pipeline/neo4j/CreateNeo4jDataset.py "$NEO4J_CONFIG"

step "Done"
