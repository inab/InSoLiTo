# Import libraries
import json
import sqlite3
import time
from os import walk

# Start time - Just to count how much the script lasts
start_time = time.time()

# Name of the database
DB_FILE = "database/MetaGraph.db"

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

# Create Tools-Citations table - It will be used to create Tools-Citations edges
# name: Name of Tool
# Publication_id: Id of a Publication
# n_citations: Number of citations from all the publications of the tools to the other publications
# year: Year of the co-occurence
c.execute('''DROP TABLE IF EXISTS Tools_to_Citations''')
c.execute('''CREATE TABLE IF NOT EXISTS "Tools_to_Citations" (
                "name" TEXT NOT NULL,
                "Publication_id" TEXT NOT NULL,
                "n_citations" INTEGER NOT NULL,
                "year" INTEGER NOT NULL,
                FOREIGN KEY("name") REFERENCES "Tools"("name"),
                FOREIGN KEY("Publication_id") REFERENCES "Publications"("id")
            )''')


def retrieve_Tools_Citations(name_tool,id_publication, dict_publications):
    # ID Publication as id1
    c.execute(f'''select id1,id2, n_citations, year
                    from Citations as c
                    where c.id1 == "{id_publication}"''')
    output=c.fetchall()
    for i in output:
        cite = f"{name_tool}\t{i[1]}\t{i[3]}"
        if cite not in dict_publications:
            dict_publications[cite] = i[2]
        else:
            dict_publications[cite] += i[2]
    
    # ID Publication as id2
    c.execute(f'''select id1,id2, n_citations, year
                    from Citations as c
                    where c.id2 == "{id_publication}"''')
    output=c.fetchall()
    for i in output:
        cite = f"{name_tool}\t{i[0]}\t{i[3]}"
        if cite not in dict_publications:
            dict_publications[cite] = i[2]
        else:
            dict_publications[cite] += i[2]
    return dict_publications

def Create_tools():
    ### Import data

    # For each folder and each file inside the folder
    counter = 0 # Dummy counter

    mypath = "PubEnricher/opeb-enrichers-master/pubEnricher/output/pruebaSAguilo/tools"
    _, _, filenames = next(walk(mypath))

    #mypath2 = "PubEnricher/pruebaSAguiloeuro/tools"
    #l_paths = [mypath1, mypath2]

    #for mypath in l_paths:
        #_, _, filenames = next(walk(mypath))

    # For loop for all the files in tools folder
    for files in filenames:
        json_file = f"{mypath}/{files}"
        json_loaded = json.load(open(json_file)) # Load the JSON file
        
        name_tool = json_loaded["@id"]
        if name_tool.startswith("https://"):
            name_tool = name_tool.split("/")[5]
        # Insert Tool in database
        c.execute(f'''INSERT INTO Tools
                        values ("{name_tool}")''')
        
        all_publications = json_loaded["entry_pubs"]
        dict_publications = {}
        # For all the publications in a tool file
        for publication in all_publications:
            publication_information = publication["found_pubs"]
            id_publication = publication_information[0]["id"]
            if id_publication is None: # If there is not any publication, use the pmid that is at the end of the file
                id_publication = publication["pmid"]
            #Insert tool-publicationid for the edges
            c.execute(f'''INSERT INTO Tools_to_Publications
                        values ("{name_tool}","{id_publication}")''')
            # Search in the publication, all its citations
            dict_publications = retrieve_Tools_Citations(name_tool,id_publication, dict_publications)
        for citation in dict_publications:
            values=citation.split("\t")
            c.execute(f'''INSERT INTO Tools_to_Citations
                        values ("{values[0]}","{values[1]}", {dict_publications[citation]}, {values[2]})''')
            
        counter+=1
        print(counter)
    conn.commit()
    c.close()

if __name__ == '__main__':
    Create_tools()
    
    print("--- %s seconds ---" % (time.time() - start_time))

