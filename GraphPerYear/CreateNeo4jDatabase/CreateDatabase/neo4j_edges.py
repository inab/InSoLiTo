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
        # Delete all the previous Publication-Publication edges
        session.run("""MATCH ()-[r:OCCUR]->() DELETE r""")
    
    #Creating Publication-Publication edges
    # :OCCUR: Label of the edge
    # times: Number of co-occurences between the two publications
    # year: Year when the co-occurence happened
    print("Creating Publication-Publication edges")
    try:
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Citations_year.csv" AS csv
            MATCH (p1:Publication {id:csv.id1}), (p2:Publication {id:csv.id2})
            CREATE (p1)-[o:OCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p2)
            """)
    except:
        print("----> Error creating Publication-Publication edges")

if __name__ == '__main__':
    graph()
    print("--- %s seconds ---" % (time.time() - start_time))
