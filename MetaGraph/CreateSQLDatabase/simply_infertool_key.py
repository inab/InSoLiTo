# Import libraries
import sqlite3
import time
import json
from owlready2 import *

# Start time - Just to count how much the script lasts
start_time = time.time()

# Name of the database
DB_FILE = "database/Namedatabase.db"

# Connect to the SQLite database
# If name not found, it will create a new database
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

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
    for keywords in set_keywords:
        name=keywords.split("/")[3]
        label = f"onto.{name}.label"
        labels = eval(label)
        for label in labels:
            c.execute(f"""INSERT OR IGNORE INTO Keywords
                            values ('{keywords}', '{label}')""")
    

def retrieve_topic(topics):
    for topic in topics:
        name=topic.split("/")[3]
        Ids = f"onto.{name}.hasHumanReadableId"
        try:
            Ids=eval(Ids)
            for Id in Ids:
                c.execute(f"""INSERT OR IGNORE INTO Keywords
                            values ('{topic}', '{Id}')""")
        except:
            continue
    

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

    retrieve_topic(set_topics)
    
    retrieve_in_out_operations(set_inputs_data)
    retrieve_in_out_operations(set_inputs_format)
    retrieve_in_out_operations(set_outputs_data)
    retrieve_in_out_operations(set_outputs_format)
    retrieve_in_out_operations(set_operations)
    
    
    list_keywords = [set_inputs_data, set_inputs_format, set_outputs_data, set_outputs_format, set_topics, set_operations]
    
    return list_keywords
    
    
# This function search in the JSON file if one of the IDs matches a publication of a tool.
def search_json(data,doi,pmid,pmcid):
    for publication in data:
        if "publications" not in publication:
            continue
        for ids in publication["publications"]:
            if "languages" not in publication:
                publication["languages"] = []
            if "os" not in publication:
                publication["os"] = []
            if doi != "None" and "doi" in ids:
                if doi in ids["doi"]:
                    list_keywords=retrieve_keywords(publication)
                    return publication["name"], publication["@label"], publication["languages"], publication["os"], list_keywords
            if pmid != "None" and "pmid" in ids:
                if pmid in ids["pmid"]:
                    list_keywords=retrieve_keywords(publication)
                    return publication["name"], publication["@label"], publication["languages"], publication["os"], list_keywords
            if pmcid != "None" and "pmcid" in ids:
                if pmcid in ids["pmcid"]:
                    list_keywords=retrieve_keywords(publication)
                    return publication["name"], publication["@label"], publication["languages"], publication["os"], list_keywords
    return False, False, False, False, False

def insert_keywords(name, keywords, name_table):
    for keyword in keywords:
        c.execute(f""" INSERT OR IGNORE INTO {name_table}
                            values ('{name}', '{keyword}')""")

def create_InferedTools():
    # Select publications that are in table Citations
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
        l_languages = []
        l_os = []
        # For each publication in Neo4j
        for i in publications:
            counter += 1
            print(counter)
            id_publication = i[0]
            name_tool, label, languages, operative_systems, list_keywords= search_json(data, str(i[1]), str(i[2]), str(i[3])) # Input the IDs of the publication from different platforms
            if not name_tool:
                continue
            # If the tool is found, we can input it in the database
            c.execute(f"""INSERT OR IGNORE INTO InferedTools
                            values ('{name_tool}', '{label}')""")
            if languages:
                for language in languages:
                    if language not in l_languages:
                        c.execute(f"""INSERT INTO Languages
                                  VALUES ('{language}')""")
                        l_languages.append(language)
                    c.execute(f"""INSERT OR IGNORE INTO InferedTools_to_Languages
                                VALUES ('{language}', '{name_tool}')""")
            if operative_systems:
                for op_sys in operative_systems:
                    if op_sys not in l_os:
                        c.execute(f"""INSERT INTO Operative_systems
                                  VALUES ('{op_sys}')""")
                        l_os.append(op_sys)
                    c.execute(f"""INSERT OR IGNORE INTO InferedTools_to_OS
                                VALUES ('{op_sys}', '{name_tool}')""")
                        
            if list_keywords:
                insert_keywords(name_tool, list_keywords[0], 'Input_data')
                insert_keywords(name_tool, list_keywords[1], 'Input_format')
                insert_keywords(name_tool, list_keywords[2], 'Output_data')
                insert_keywords(name_tool, list_keywords[3], 'Output_format')
                insert_keywords(name_tool, list_keywords[4], 'Topics')
                insert_keywords(name_tool, list_keywords[5], 'Operations')

                
                    
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

    # Sort the values in columns to sum well all the citations
    c.execute("""
        UPDATE MetaCitations
            SET id1 = id2, 
            id2 = id1
            WHERE id1 > id2
        """)

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

