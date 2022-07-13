# Import libraries
import sqlite3
import time
import sys


# Import functions
from CreateTables import create_SQL_tables
from RetrievePublications import retrieve_publications
from CalculateCitations import calculate_citations
from InferToolsKeywords import create_Tools
from AddEDAMSubclasses import create_EDAM_table

# Start time - Just to count how much the script lasts
start_time = time.time()

# Name of the database
DB_FILE = f"{sys.argv[1]}.db"

# Name of the output folder from PubEnricher.py
folderpath = sys.argv[2]

# Connect to the SQLite database
# If name not found, it will create a new database
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()


def main():
    print(f"Creating tables in '{DB_FILE}' database")
    create_SQL_tables(c)
    conn.commit()
    print("Storing all publications")
    retrieve_publications(folderpath, c)
    conn.commit()
    c.execute('''
    CREATE UNIQUE INDEX idx_Publications
    ON Publications(doi) WHERE doi IS NOT NULL;
    ''')
    print("Calculate co-occurrences between publications")
    calculate_citations(folderpath, c, conn)
    conn.commit()
    print("Infer Tools and Keywords")
    create_Tools(c,conn)
    conn.commit()
    print("Create a Keywords hierarchy")
    create_EDAM_table(c,conn)
    conn.commit()


if __name__ == '__main__':
    main()
    print("--- %s seconds ---" % (time.time() - start_time))
    c.close()
