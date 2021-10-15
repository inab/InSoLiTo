# Import libraries
import json
import sqlite3
import itertools
import time
from os import walk

# Start time - Just to count how much the script lasts
start_time = time.time()

# Name of the database
DB_FILE = "database/Namedatabase.db"

# Connect to the SQLite database
# If name not found, it will create a new database
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

counter = 0 # Dummy counter

mypath = "Path/PublicationsDomain"

_, dirnames, _ = next(walk(mypath))


for folder in dirnames:
    if not folder.startswith("pubs_"): # Only take folders with publications
        continue
    _, _, filenames = next(walk(f"{mypath}/{folder}/"))
    # For each file in folder
    for files in filenames:
        json_file = f"{mypath}/{folder}/{files}"
        
        traffic = json.load(open(json_file)) # Open JSON of each publication

        # Retrieve IDs
        l = [i["id"]for i in traffic["reference_refs"] if i["id"]]
        if "year" not in traffic:
            continue
        
        # Compute all possible combinations
        pos_comb = [subset for subset in itertools.combinations(l,2)]
        
        # Insert the citations in the database
        for comb in pos_comb:
            c.execute(f'''
                    INSERT INTO Citations (id1, id2, n_citations, year)
                    VALUES ("{comb[0]}", "{comb[1]}", 1, {traffic["year"]})
                    ''')
        counter+=1
        print(counter)
        conn.commit()
    # Sum all the citations with the same values
    # The sum must be > 1 to store it in the database
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
# When the process is finished, store the Publication-Publication edges with more than 10 citations
c.execute("""
    CREATE TABLE Citations_backup AS
    Select id1,id2, sum(n_citations) as n_citations, year
    from Citations
    group by id1, id2, year
    HAVING sum(n_citations) > 10
    """)
c.execute("""DROP TABLE Citations""")
c.execute("""
    ALTER TABLE Citations_backup
    RENAME TO Citations;
    """)
conn.commit()

c.close()

print("--- %s seconds ---" % (time.time() - start_time))
