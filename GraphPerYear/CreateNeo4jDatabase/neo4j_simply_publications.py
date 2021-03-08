from neo4j import GraphDatabase
import time
import json

# Start time - Just to count how much the script lasts
start_time = time.time()

# URL of the Neo4j Server
uri = "bolt://localhost:7687"
# Driver to connect to the Server with the author and the password
# To be able to use it, you need to open your neo4j server before
driver = GraphDatabase.driver(uri, auth=("neo4j", "1234"))

# This function search in the JSON file if one of the IDs matches a publication of a tool.
def search_json(data,doi,pmid,pmcid):
    for i in data:
        if "publications" not in i:
            continue
        for ids in i["publications"]:
            if doi != "None" and "doi" in ids:
                if doi in ids["doi"]:
                    return i["name"]
            if pmid != "None" and "pmid" in ids:
                if pmid in ids["pmid"]:
                    return i["name"]
            if pmcid != "None" and "pmcid" in ids:
                if pmcid in ids["pmcid"]:
                    return i["name"]

def graph():
    with driver.session() as session:
        # Delete all the nodes with no edges
        session.run("""
            MATCH (n)
            WHERE size((n)--())=0
            DELETE (n)
            """)
    try:
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
                name_tool= search_json(data, i["doi"], i["pmid"], i["pmcid"]) # Input the IDs of the publication from different platforms
                if not name_tool:
                    continue
                # If the tool is found, we can input it in the database
                query ="""
                    match (n:Publication {id: "%s"})
                    create (n)-[:HAS_TOOL]->(:InferedTool {name:"%s"})
                    """ % (i["id"], name_tool)
                session.run(query)
    except:
        print("Doesn't work")

if __name__ == '__main__':
    graph()
    print("--- %s seconds ---" % (time.time() - start_time))

