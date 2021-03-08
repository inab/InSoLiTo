# Import libraries
from neo4j import GraphDatabase
import time
import json
import urllib.request as request

# Start time - Just to count how much the script lasts
start_time = time.time()

# URL of the Neo4j Server
uri = "bolt://localhost:7687"
# Driver to connect to the Server with the author and the password
# To be able to use it, you need to open your neo4j server before
driver = GraphDatabase.driver(uri, auth=("neo4j", "1234"))

# Search for EDAM keywords
def retrieve_keywords(data):
    l_keywords = set()
    for count in data["list"]:
        for keys in count["topic"]:
            l_keywords.add(keys["term"])
        for function in count["function"]:
            if "input" in function:
                for input in function["input"]:
                    l_keywords.add(input["data"]["term"])
            if "operation" in function:
                for operation in function["operation"]:
                    l_keywords.add(operation["term"])
            if "output" in function:
                for output in function["output"]:
                    l_keywords.add(output["data"]["term"])
    return l_keywords        

# Search each publication ID in the bio.tools API
def search_json(list_pos_ids):
    for id_type in range(len(list_pos_ids)):
        url = f'https://bio.tools/api/t/?publicationID="{list_pos_ids[id_type]}"&format=json'
        response = request.urlopen(url)
        data = json.loads(response.read())
        if data["count"] == 0:
            continue
        keywords = retrieve_keywords(data)
        # Search name of tool
        for count in data["list"]:
            if "(EBI)" in  count["name"]:
                continue
            return count["name"], keywords
    return False, False

def graph():
    with driver.session() as session:
        # Delete all the nodes with no edges
        session.run("""
            MATCH (n)
            WHERE size((n)--())=0
            DELETE (n)
            """)
        # Return all publication IDs that doesn't have an edge with any Tool
        publications = session.run("""
            match (n)
            where not (n)-[:HAS_TOOL]-()
            return n.id as id , n.pmid as pmid, n.doi as doi, n.pmcid as pmcid
            """)
        counter = 0
        for i in publications:
            counter += 1
            print(counter)
            list_ids =[]
            if i["doi"] != "None":
                list_ids.append(i["doi"])
            if i["pmid"] != "None":
                list_ids.append(i["pmid"])
            if i["pmcid"] != "None":
                list_ids.append(i["pmcid"])
            name_tool,keywords= search_json(list_ids)
            if not name_tool:
                continue
            print(name_tool, keywords)
            keywords = list(keywords)
            # If we have the name of the query, we can insert it to the Neo4j database
            query ="""
                match (n:Publication {id: "%s"})
                create (n)-[:HAS_TOOL]->(:InferedTool {name:"%s",keywords: %s})
                """ % (i["id"], name_tool, keywords)
            session.run(query)

if __name__ == '__main__':
    graph()
    print("--- %s seconds ---" % (time.time() - start_time))
