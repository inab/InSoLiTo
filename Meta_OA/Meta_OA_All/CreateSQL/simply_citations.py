# Import libraries
import json
import sqlite3
import itertools
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

list_labels = ["Comp","Mol","Prot"]
list_databases = ["MetaGraph","MetaMolecular","MetaProteomics"]

for label_index in range(len(list_labels)):
    c.execute(f"ATTACH DATABASE 'database/{list_databases[label_index]}.db' AS {list_labels[label_index]};")
    c.execute(f"\
        INSERT INTO Citations \
        (id1, id2, n_citations, year) \
        SELECT id1, id2, n_citations, year \
        FROM {list_labels[label_index]}.MetaCitations ;")
    conn.commit()

c.execute("""
    CREATE TABLE Citations_backup AS
    Select id1,id2, sum(n_citations) as n_citations, year
    from Citations
    group by id1, id2, year
    HAVING sum(n_citations) > 1
    """)
# We drop the table and then change the name to update the table
c.execute("""DROP TABLE Citations""")
c.execute("""
    ALTER TABLE Citations_backup
    RENAME TO Citations;
    """)
conn.commit()


# Insert the sections from the OpenAccess
list_sections = ["Discussion", "Introduction", "Methods", "Results"]
list_databases = ["OAComparative","OAMolecular","OAProteomics"]

for index_databases in range(len(list_databases)):        
    c.execute(f"ATTACH DATABASE 'database/{list_databases[index_databases]}.db' AS {list_databases[index_databases]};")

for index_sections in range(len(list_sections)):
    for index_databases in range(len(list_databases)):        
        c.execute(f"\
            INSERT INTO Citations_{list_sections[index_sections]} \
            (id1, id2, n_citations, year) \
            SELECT id1, id2, n_citations, year \
            FROM {list_databases[index_databases]}.MetaCitations_{list_sections[index_sections]} ;")
        conn.commit()

    c.execute(f"""
        CREATE TABLE Citations_{list_sections[index_sections]}_backup AS
        Select id1,id2, sum(n_citations) as n_citations, year
        from Citations_{list_sections[index_sections]}
        group by id1, id2, year
        having sum(n_citations) > 1
        """)
    # We drop the table and then change the name to update the table
    c.execute(f"""DROP TABLE Citations_{list_sections[index_sections]}""")
    c.execute(f"""
        ALTER TABLE Citations_{list_sections[index_sections]}_backup
        RENAME TO Citations_{list_sections[index_sections]};
        """)
    conn.commit()

c.close()

print("--- %s seconds ---" % (time.time() - start_time))


