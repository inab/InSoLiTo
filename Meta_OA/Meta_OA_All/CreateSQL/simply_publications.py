# Import libraries
import json
import sqlite3
import time
from os import walk

# Start time - Just to count how much the script lasts
start_time = time.time()

# Name of the database
DB_FILE = "database/All_META_OA.db"

# Connect to the SQLite database
# If name not found, it will create a new database
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Create Publications table - It will be used to create Publication nodes
# id: Primary key of the publication
# title: Title of the publication
# year: Year of the publication
# pmcid: PMCID of the publication
# pmid: PMID of the publication
# doi: DOI of the publication
c.execute('''DROP TABLE IF EXISTS Publications''')
c.execute('''CREATE TABLE IF NOT EXISTS "Publications" (
	            "id"	TEXT NOT NULL,
	            "title"	TEXT NOT NULL,
	            "year" INTEGER,
	            "pmcid" TEXT,
	            "pmid" TEXT,
	            "doi" TEXT,
	            PRIMARY KEY("id")
            )''')
c.execute('''
    CREATE UNIQUE INDEX idx_Publications
    ON Publications (doi, pmcid, pmid);
    ''')

c.execute("ATTACH DATABASE 'database/MetaGraph.db' AS Comp;")
c.execute("\
    INSERT INTO Publications \
    (id, title, year, pmcid, pmid, doi) \
    SELECT id, title, year, pmcid, pmid, doi \
    FROM Comp.Publications ;")
conn.commit()

c.execute("ATTACH DATABASE 'database/MetaMolecular.db' AS Mol;")
c.execute("\
    INSERT OR IGNORE INTO Publications \
    (id, title, year, pmcid, pmid, doi) \
    SELECT id, title, year, pmcid, pmid, doi \
    FROM Mol.Publications ;")
conn.commit()

c.execute("ATTACH DATABASE 'database/MetaProteomics.db' AS Prot;")
c.execute("\
    INSERT OR IGNORE INTO Publications \
    (id, title, year, pmcid, pmid, doi) \
    SELECT id, title, year, pmcid, pmid, doi \
    FROM Prot.Publications ;")
conn.commit()

c.close()

print("--- %s seconds ---" % (time.time() - start_time))
