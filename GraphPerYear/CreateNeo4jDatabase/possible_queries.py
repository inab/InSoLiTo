# Import libraries
from neo4j import GraphDatabase
import itertools
import sys

# URL of the Neo4j Server
uri = "bolt://localhost:7687"
# Driver to connect to the Server with the author and the password
# To be able to use it, you need to open your neo4j server before
driver = GraphDatabase.driver(uri, auth=("neo4j", "1234"))

def stats_graph():
    with driver.session() as session:
        # Subworkflows
        print("Retrieving sub-workflows")
        try:
            session.run("""
                MATCH (n)-[o:OCCUR]-(p1)
                WHERE 1992 <=o.year <=1993
                WITH n, p1, collect(o) as co
                unwind co as c
                with sum(c.times) as sumo, n,p1, co
                RETURN n, sumo,co, p1 Limit 10
                """
                
        except:
            print("----> Error creating Retrieving sub-workflows")
            

if __name__ == '__main__':
    stats_graph()
