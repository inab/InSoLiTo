# Import libraries
import json
import sqlite3
import time
from os import walk

# Start time - Just to count how much the script lasts
start_time = time.time()

# Name of the database
DB_FILE = "database.db"

# Connect to the SQLite database
# If name not found, it will create a new database
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Create Tools table - It will be used to create Tool nodes
# name: Name of the tool
c.execute('''DROP TABLE IF EXISTS Tools''')
c.execute('''CREATE TABLE IF NOT EXISTS "Tools" (
                "name" TEXT NOT NULL,
                PRIMARY KEY("name")

            )''')


# Create Tools-Publications table - It will be used to create Tools-Publications edges
# name: Name of Tool
# Publication_id: Id of a Publication
c.execute('''DROP TABLE IF EXISTS Tools_to_Publications''')
c.execute('''CREATE TABLE IF NOT EXISTS "Tools_to_Publications" (
                "name" TEXT NOT NULL,
                "Publication_id" TEXT NOT NULL,
                FOREIGN KEY("name") REFERENCES "Tools"("name"),
                FOREIGN KEY("Publication_id") REFERENCES "Publications"("id")
            )''')


### Import data

# For each folder and each file inside the folder
counter = 0 # Dummy counter

mypath = "PubEnricher/opeb-enrichers-master/pubEnricher/output/pruebaSAguilo/tools"
_, _, filenames = next(walk(mypath))

# For loop for all the files in tools folder
for files in filenames:
    json_file = f"{mypath}/{files}"
    json_loaded = json.load(open(json_file)) # Load the JSON file
    
    name_tool = json_loaded["@id"]
    
    # Insert Tool in database
    c.execute(f'''INSERT INTO Tools
                    values ("{name_tool}")''')
    
    all_publications = json_loaded["entry_pubs"]
    # For all the publications in a tool file
    for publication in all_publications:
        publication_information = publication["found_pubs"]
        id_publication = publication_information[0]["id"]
        if id_publication is None: # If there is not any publication, use the pmid that is at the end of the file
            id_publication = publication["pmid"]
        
        #Insert tool-publicationid for the edges
        c.execute(f'''INSERT INTO Tools_to_Publications
                    values ("{name_tool}","{id_publication}")''')
    counter+=1
    print(counter)
conn.commit()
c.close()

print("--- %s seconds ---" % (time.time() - start_time))
