from neo4j import GraphDatabase
import time
import json
from owlready2 import *

# Start time - Just to count how much the script lasts
start_time = time.time()

# URL of the Neo4j Server
uri = "bolt://localhost:7687"
# Driver to connect to the Server with the author and the password
# To be able to use it, you need to open your neo4j server before
driver = GraphDatabase.driver(uri, auth=("neo4j", "1234"))

def retrieve_keywords(i):
    set_keywords = set()
    if "semantics" not in i:
        return False
    for inputs in i["semantics"]["inputs"]:
        if "datatype" in inputs:
            set_keywords.add(inputs["datatype"])
        for formats in inputs["formats"]:
            set_keywords.add(formats)
    for operations in i["semantics"]["operations"]:
        set_keywords.add(operations)
    for outputs in i["semantics"]["outputs"]:
        if "datatype" in outputs:
            set_keywords.add(outputs["datatype"])
        for formats in outputs["formats"]:
            set_keywords.add(formats) 
    for topics in i["semantics"]["topics"]:
        set_keywords.add(topics)
    set_names= set()
    for keywords in set_keywords:
        name=keywords.split("/")[3]
        if "topic" in name:
            Ids = f"onto.{name}.hasHumanReadableId"
            try:
                Ids=eval(Ids)
                for Id in Ids:
                    Id=Id.replace("_", " ")
                    set_names.add(Id)
            except:
                continue
            continue
        label = f"onto.{name}.label"
        labels = eval(label)
        for label in labels:
            label = label.replace("_", " ")
            set_names.add(label)
    print(set_names)
    return list(set_names)
    
    
# This function search in the JSON file if one of the IDs matches a publication of a tool.
def search_json(data,doi,pmid,pmcid):
    for i in data:
        if "publications" not in i:
            continue
        if "(EBI)" in i["name"]:
            continue
        for ids in i["publications"]:
            if doi != "None" and "doi" in ids:
                if doi in ids["doi"]:
                    keywords=retrieve_keywords(i)
                    return i["name"], keywords
            if pmid != "None" and "pmid" in ids:
                if pmid in ids["pmid"]:
                    keywords=retrieve_keywords(i)
                    return i["name"], keywords
            if pmcid != "None" and "pmcid" in ids:
                if pmcid in ids["pmcid"]:
                    keywords=retrieve_keywords(i)
                    return i["name"], keywords
    return False, False

def graph():
    with driver.session() as session:
        # Delete all the nodes with no edges
        session.run("""
            MATCH (n)
            WHERE size((n)--())=0
            DELETE (n)
            """)

        # Take publications that do not have any edge with a Tool node
        publications = session.run("""
            match (n)
            where not (n)-[:HAS_TOOL]-()
            return n.id as id , n.pmid as pmid, n.doi as doi, n.pmcid as pmcid
            """)
        # Open the file with all the tools with publications in OpenEBench
        # File is following API search: "https://openebench.bsc.es/monitor/rest/search?=publications"
        with open("publications.json") as json_file:
            data = json.load(json_file)
            counter = 0 # Dummy counter
            # For each publication in Neo4j
            for i in publications:
                counter += 1
                print(counter)
                name_tool, keywords= search_json(data, i["doi"], i["pmid"], i["pmcid"]) # Input the IDs of the publication from different platforms
                if not name_tool:
                    continue
                # If the tool is found, we can input it in the database
                l_keywords = []
                if keywords:
                    l_keywords = list(keywords)
                print(i["id"], name_tool, l_keywords)
                query ="""
                    match (n:Publication {id: "%s"})
                    create (n)-[:HAS_TOOL]->(:InferedTool {name:"%s", keywords: %s})
                    """ % (i["id"], name_tool, l_keywords)
                session.run(query)

if __name__ == '__main__':
    # Import ontology
    onto = get_ontology("http://edamontology.org/EDAM.owl").load()
    graph()
    print("--- %s seconds ---" % (time.time() - start_time))

