# Import libraries
import sqlite3
import time
import sys


# Import functions
from CreateTables import create_SQL_tables
from RetrievePublications import retrieve_publications
from CalculateCitations import calculate_citations
from InferToolsKeywords import create_Tools, load_oeb
from AddEDAMSubclasses import create_EDAM_table

# Start time - Just to count how much the script lasts
start_time = time.time()

# Optional flag: keep the Publications table of an existing database and skip the first pass over PubMed
REUSE_PUBLICATIONS = "--reuse-publications" in sys.argv
args = [a for a in sys.argv[1:] if a != "--reuse-publications"]

# Name of the database
DB_FILE = f"{args[0]}.db"

# Folder with the PubMed baseline files (.xml.gz)
folderpath = args[1]

# Optional: local OpenEBench JSON snapshot. If missing, it is downloaded
oeb_path = args[2] if len(args) > 2 else None

# Connect to the SQLite database
# If name not found, it will create a new database
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()


def main():
    # Loaded once: step 3 needs the tool papers too, not only create_Tools()
    print("Loading OpenEBench tools")
    oeb_data = load_oeb(oeb_path)
    print(f"Creating tables in '{DB_FILE}' database")
    create_SQL_tables(c, keep_publications=REUSE_PUBLICATIONS)
    conn.commit()
    if REUSE_PUBLICATIONS:
        if c.execute("SELECT 1 FROM Publications LIMIT 1").fetchone() is None:
            sys.exit("--reuse-publications: the Publications table is empty or missing")
        print("Reusing the existing Publications table")
    else:
        print("Storing all publications")
        retrieve_publications(folderpath, c)
        conn.commit()
    c.execute('''
    CREATE UNIQUE INDEX IF NOT EXISTS idx_Publications
    ON Publications(doi) WHERE doi IS NOT NULL;
    ''')
    print("Calculate co-occurrences between publications")
    calculate_citations(folderpath, c, conn, oeb_data)
    conn.commit()
    # create_Tools() rewrites MetaCitations, but no script created it:
    # it starts as a copy of Citations
    c.execute('''DROP TABLE IF EXISTS MetaCitations''')
    c.execute('''CREATE TABLE MetaCitations AS SELECT * FROM Citations''')
    conn.commit()
    print("Infer Tools and Keywords")
    create_Tools(c, conn, oeb_data)
    conn.commit()
    print("Create a Keywords hierarchy")
    create_EDAM_table(c,conn)
    conn.commit()


if __name__ == '__main__':
    main()
    print("--- %s seconds ---" % (time.time() - start_time))
    c.close()
