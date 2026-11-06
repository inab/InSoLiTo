# Export the SQLite tables that the Neo4j import needs to CSV files
# Usage: python export_csv.py <database.db> <output folder>
import csv
import sqlite3
import sys
from pathlib import Path

# Same tables (and file names) as DB/Neo4jScripts/sample-config.ini
TABLES = [
    "PublicationsInMetaCitations", "MetaCitationsReduction", "Keywords",
    "Tools", "TypeTool", "ToolsToTypeTool", "Languages", "ToolsToLanguages",
    "OperativeSystems", "ToolsToOS", "InputData", "InputFormat",
    "OutputData", "OutputFormat", "Topics", "Operations",
    "SubclassEDAM", "ToolsToPublications",
]

db_file = sys.argv[1]
out_dir = Path(sys.argv[2])
out_dir.mkdir(parents=True, exist_ok=True)

c = sqlite3.connect(db_file).cursor()
for table in TABLES:
    c.execute(f"SELECT * FROM {table}")
    header = [col[0] for col in c.description]
    with open(out_dir / f"{table}.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        rows = c.fetchall()
        writer.writerows(rows)
    print(f"{table}: {len(rows)} rows")
