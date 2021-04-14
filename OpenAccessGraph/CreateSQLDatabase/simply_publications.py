# Import libraries
import json
import sqlite3
import time
from os import walk

# Start time - Just to count how much the script lasts
start_time = time.time()

# Name of the database
DB_FILE = "database/OAComparative.db"

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

### Import data
counter = 0 # Dummy counter

mypath = "PubEnricher/opeb-enrichers-master/pubEnricher/output/pruebaSAguilo"
#mypath = "PubEnricher/pruebaSAguiloAPE_2"
#mypath = "PubEnricher/pruebaSAguiloeuro_MoL"


_, dirnames, _ = next(walk(mypath))

#l_paths = [mypath1, mypath2]

#for mypath in l_paths:
    #_, dirnames, _ = next(walk(mypath))

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
