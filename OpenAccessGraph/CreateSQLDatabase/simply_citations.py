# Import libraries
import json
import sqlite3
import itertools
import time
from os import walk

# Start time - Just to count how much the script lasts
start_time = time.time()

# Name of the database
DB_FILE = "database/OAProteomics.db"



# Connect to the SQLite database
# If name not found, it will create a new database
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

list_labels = ["Discussion", "Introduction", "Methods", "Results"]

for label in list_labels:
    c.execute(f"""DROP TABLE IF EXISTS Citations_{label}_backup""")
    print(f"Computing table {label}")
    # Sum all the citations with the same values
    # The sum must be > 1 to store it in the database
    c.execute(f"""
        CREATE TABLE Citations_{label}_backup AS
        Select id1,id2, sum(n_citations) as n_citations, year
        from Citations_{label}
        group by id1, id2, year
        having sum(n_citations) > 1
        """)
    # We drop the table and then change the name to update the table
    #c.execute(f"""DROP TABLE Citations_{label}""")
    #c.execute(f"""
        #ALTER TABLE Citations_{label}_backup
        #RENAME TO Citations_{label};
        #""")
    conn.commit()



c.close()

print("--- %s seconds ---" % (time.time() - start_time))


