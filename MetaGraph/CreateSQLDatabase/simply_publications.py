# Import libraries
import json
import sqlite3
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


### Import data
counter = 0 # Dummy counter

mypath = "Path/PublicationsDomain"

_, dirnames, _ = next(walk(mypath))


# For each folder
for folder in dirnames:
    if not folder.startswith("pubs_"): # Only take folders with publications
        continue
    _, _, filenames = next(walk(f"{mypath}/{folder}/"))
    # For each file inside the folder
    for files in filenames:
        json_file = f"{mypath}/{folder}/{files}"
        
        traffic = json.load(open(json_file)) # Open JSON of each publication
        if "title" not in traffic:
            continue
        title = traffic["title"].replace('"', "'") # Standarize the quotation marks
        #Insert Publication information into the database
        c.execute(f'''INSERT OR REPLACE INTO Publications
                    VALUES ("{traffic["id"]}","{title}",{traffic["year"]},"{traffic["pmcid"]}", "{traffic["pmid"]}", "{traffic["doi"]}")''')
        counter+=1
        print(counter)
    conn.commit()
c.close()

print("--- %s seconds ---" % (time.time() - start_time))
