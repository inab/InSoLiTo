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
        session.run("""MATCH ()-[r:METAOCCUR]->() DELETE r""")

        print("InferedTool-Publication citations")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///MetaCitations.csv" AS csv
            MATCH (t:InferedTool {name:csv.id1}),(p:Publication {id:csv.id2})
            CREATE (t)-[:METAOCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p)
        """)
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///MetaCitations.csv" AS csv
            MATCH (t:InferedTool {name:csv.id2}),(p:Publication {id:csv.id1})
            CREATE (t)-[:METAOCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p)
        """)
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///MetaCitations.csv" AS csv
            MATCH (t:InferedTool {name:csv.id1}),(t2:InferedTool {name:csv.id2})
            CREATE (t)-[:METAOCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(t2)
        """)
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///MetaCitations.csv" AS csv
            MATCH (p:Publication {id:csv.id1}),(p2:Publication {id:csv.id2})
            CREATE (p)-[:METAOCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p2)
        """)

if __name__ == '__main__':
    graph()
    print("--- %s seconds ---" % (time.time() - start_time))
