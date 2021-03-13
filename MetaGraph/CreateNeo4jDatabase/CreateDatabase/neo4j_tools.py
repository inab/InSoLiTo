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
        # Delete all the previous Tool related nodes and edges
        session.run("""MATCH ()-[r:HAS_TOOL]-() DELETE r""")
        session.run("""MATCH (r:Tool) DELETE r""")

    
    #Creating Tools nodes
    # :Tool: Label of the nodes
    # name: Name of the tool
    print("Creating Tool nodes")
    try:
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Tools.csv" AS csv
            CREATE (:Tool {name: csv.name})
            """)
    except:
        print("----> Error creating Tool nodes")

    #Creating Tool-Publications edges
    # :HAS_TOOL: Label of the edges
    print("Creating Tool-Publication edges")
    try:
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Tools_to_Publications.csv" AS csv
            MATCH (t:Tool {name:csv.name}),(p:Publication {id:csv.Publication_id})
            CREATE (p)-[:HAS_TOOL]->(t)
            """)
    except:
        print("----> Error creating Tool-Publication edges")

    #Creating Tool-Citation edges
    # :OCCUR: Label of the edges
    print("Creating Tool-Citations edges")
    try:
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Tools_to_Citations.csv" AS csv
            MATCH (t:Tool {name:csv.name}),(p:Publication {id:csv.Publication_id})
            CREATE (t)-[:OCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p)
            """)
    except:
        print("----> Error creating Tool-Citations edges")  

if __name__ == '__main__':
    graph()
    print("--- %s seconds ---" % (time.time() - start_time))
