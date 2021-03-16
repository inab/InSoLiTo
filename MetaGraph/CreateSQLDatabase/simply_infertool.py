# Import libraries
import sqlite3
import time
import json
from owlready2 import *
import itertools

# Start time - Just to count how much the script lasts
start_time = time.time()

# Name of the database
DB_FILE = "database/MetaGraph.db"

# Connect to the SQLite database
# If name not found, it will create a new database
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Create InferedTools table - It will be used to create Tool nodes
# name: Name of the InferedTool
c.execute('''DROP TABLE IF EXISTS InferedTools''')
c.execute('''CREATE TABLE IF NOT EXISTS "InferedTools" (
                "name" TEXT NOT NULL,
	            PRIMARY KEY("name")
            )''')

# Create InferedTools table - It will be used to create Tool nodes
# name: Name of the InferedTool
c.execute('''DROP TABLE IF EXISTS InferedTools_key''')
c.execute('''CREATE TABLE IF NOT EXISTS "InferedTools_key" (
                "name" TEXT NOT NULL,
                "input_data" TEXT,
                "input_format" TEXT,
                "output_data" TEXT,
                "output_format" TEXT,
                "topics" TEXT,
                "operations" TEXT,
	            FOREIGN KEY("name") REFERENCES "InferedTools"("name")
            )''')

# Create InferedTools-Publications table - It will be used to create InferedTools-Publications edges
# name: Name of InferedTool
# Publication_id: Id of a Publication
c.execute('''DROP TABLE IF EXISTS InferedTools_to_Publications''')
c.execute('''CREATE TABLE IF NOT EXISTS "InferedTools_to_Publications" (
                "name" TEXT NOT NULL,
                "Publication_id" TEXT NOT NULL,
                FOREIGN KEY("name") REFERENCES "InferedTools"("name"),
                FOREIGN KEY("Publication_id") REFERENCES "Publications"("id")
            )''')

# Create InferedTools-Citations table - It will be used to create InferedTools-Citations edges
# name: Name of InferedTool
# Publication_id: Id of a Publication
# n_citations: Number of citations from all the publications of the tools to the other publications
# year: Year of the co-occurence
c.execute('''DROP TABLE IF EXISTS MetaCitations''')
c.execute('''CREATE TABLE MetaCitations AS
                select id1,id2, n_citations, year
                from Citations
            ''')

def retrieve_in_out_operations(set_keywords):
    set_names = set()
    for keywords in set_keywords:
        name=keywords.split("/")[3]
        label = f"onto.{name}.label"
        labels = eval(label)
        for label in labels:
            set_names.add(label)
    return set_names
    

def retrieve_topic(topics):
    name_topics = set()
    for topic in topics:
        name=topic.split("/")[3]
        Ids = f"onto.{name}.hasHumanReadableId"
        try:
            Ids=eval(Ids)
            for Id in Ids:
                Id=Id.replace("_", " ")
                name_topics.add(Id)
        except:
            continue
    return name_topics
    

def retrieve_keywords(i):
    set_inputs_data = set()
    set_inputs_format = set()
    set_outputs_data = set()
    set_outputs_format = set()
    set_topics = set()
    set_operations = set()
    if "semantics" not in i:
        return False
    for inputs in i["semantics"]["inputs"]:
        if "datatype" in inputs:
            set_inputs_data.add(inputs["datatype"])
        for formats in inputs["formats"]:
            set_inputs_format.add(formats)
    for operations in i["semantics"]["operations"]:
        set_operations.add(operations)
    for outputs in i["semantics"]["outputs"]:
        if "datatype" in outputs:
            set_outputs_data.add(outputs["datatype"])
        for formats in outputs["formats"]:
            set_outputs_format.add(formats)
    for topics in i["semantics"]["topics"]:
        set_topics.add(topics)

    set_topics = retrieve_topic(set_topics)
    
    set_inputs_data = retrieve_in_out_operations(set_inputs_data)
    set_inputs_format = retrieve_in_out_operations(set_inputs_format)
    set_outputs_data = retrieve_in_out_operations(set_outputs_data)
    set_outputs_format = retrieve_in_out_operations(set_outputs_format)
    set_operations = retrieve_in_out_operations(set_operations)
    
    list_keywords = [set_inputs_data, set_inputs_format, set_outputs_data, set_outputs_format, set_topics, set_operations]
    
    return list_keywords
    
    
# This function search in the JSON file if one of the IDs matches a publication of a tool.
def search_json(data,doi,pmid,pmcid):
    for publication in data:
        if "publications" not in publication:
            continue
        if "(EBI)" in publication["name"]:
            continue
        for ids in publication["publications"]:
            if doi != "None" and "doi" in ids:
                if doi in ids["doi"]:
                    list_keywords=retrieve_keywords(publication)
                    return publication["name"], list_keywords
            if pmid != "None" and "pmid" in ids:
                if pmid in ids["pmid"]:
                    list_keywords=retrieve_keywords(publication)
                    return publication["name"], list_keywords
            if pmcid != "None" and "pmcid" in ids:
                if pmcid in ids["pmcid"]:
                    list_keywords=retrieve_keywords(publication)
                    return publication["name"], list_keywords
    return False, False

def create_InferedTools():
    c.execute("""SELECT distinct p.id, p.doi,p.pmid,p.pmcid
                                from Publications as p, Citations as c
                                where (p.id == c.id1 or p.id == c.id2)
                                """)
    publications=c.fetchall()

    
    # Open the file with all the tools with publications in OpenEBench
    # File is following API search: "https://openebench.bsc.es/monitor/rest/search?=publications"
    with open("publications.json") as json_file:
        data = json.load(json_file)
        counter = 0 # Dummy counter
        # For each publication in Neo4j
        for i in publications:
            dict_publications = {}
            counter += 1
            print(counter)
            id_publication = i[0]
            name_tool, list_keywords= search_json(data, str(i[1]), str(i[2]), str(i[3])) # Input the IDs of the publication from different platforms
            if not name_tool:
                continue
            # If the tool is found, we can input it in the database
            c.execute(f"""INSERT OR IGNORE INTO InferedTools
                            values ('{name_tool}')""")
            if list_keywords:
                # Transpose the nested list to enter as many values as possible in each row
                list_keywords = list(map(list, itertools.zip_longest(*list_keywords, fillvalue=None)))
                for keyword in list_keywords:
                    c.execute(f"""INSERT INTO InferedTools_key
                            VALUES ('{name_tool}', '{keyword[0]}', '{keyword[1]}','{keyword[2]}','{keyword[3]}', '{keyword[4]}', '{keyword[5]}')""")
                    
            #Insert the tools that are above the publications
            c.execute(f'''INSERT INTO InferedTools_to_Publications
                    values ("{name_tool}","{id_publication}")''')
            c.execute(f'''UPDATE MetaCitations
                            SET id1 = "{name_tool}"
                            WHERE id1 = "{id_publication}" ''')
            c.execute(f'''UPDATE MetaCitations
                            SET id2 = "{name_tool}"
                            WHERE id2 = "{id_publication}" ''')
            conn.commit()

    #Sum all the n_citations from all the tools with the same values (in case we have the same co-occurence in the same year for more than one publication from a tool)
    c.execute("""
        CREATE TABLE MetaCitations_backup AS
        Select id1,id2, sum(n_citations) as n_citations, year
        from MetaCitations
        group by id1,id2, year
        """)
    #We drop the table and then change the name to update the table
    c.execute("""DROP TABLE MetaCitations""")
    c.execute("""
        ALTER TABLE MetaCitations_backup
        RENAME TO MetaCitations;
        """)
    conn.commit()


if __name__ == '__main__':
    # Import ontology
    onto = get_ontology("http://edamontology.org/EDAM.owl").load()
    create_InferedTools()
    c.close()
    print("--- %s seconds ---" % (time.time() - start_time))

