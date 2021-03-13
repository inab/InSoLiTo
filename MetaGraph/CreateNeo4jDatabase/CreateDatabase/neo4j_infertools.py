# Import libraries
from neo4j import GraphDatabase
import time

# Start time - Just to count how much the script lasts
start_time = time.time()

# URL of the Neo4j Server
uri = "bolt://localhost:7687"
# Driver to connect to the Server with the author and the password
# To be able to use it, you need to open your neo4j server before
driver = GraphDatabase.driver(uri, auth=("neo4j", "1234"))

def graph():
    with driver.session() as session:
        session.run("""MATCH ()-[r:HAS_TOOL]->() DELETE r""")
        session.run("""MATCH (r:InferedTool) DELETE r""")
        session.run("""DROP INDEX index_infertools IF EXISTS""")

        #Creating Tools nodes
        # :Tool: Label of the nodes
        # name: Name of the tool
        print("Creating InferTool nodes")

        session.run("""
            LOAD CSV WITH HEADERS FROM 'file:///InferedTools_key.csv' AS csv
            WITH DISTINCT csv.name AS csvname, COLLECT(DISTINCT csv.keywords) as csvkeywords
            CREATE (:InferedTool {name: csvname, keywords: csvkeywords})
            """)
        session.run("""
            CREATE INDEX index_infertools FOR (n:InferedTool) ON (n.name)
            """)


        #Creating Tool-Publications edges
        # :HAS_TOOL: Label of the edges
        print("Creating Tool-Publication edges")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///InferedTools_to_Publications.csv" AS csv
            MATCH (t:InferedTool {name:csv.name}),(p:Publication {id:csv.Publication_id})
            CREATE (p)-[:HAS_TOOL]->(t)
            """)



if __name__ == '__main__':
    graph()
    print("--- %s seconds ---" % (time.time() - start_time))
