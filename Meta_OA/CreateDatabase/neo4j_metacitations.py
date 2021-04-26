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
       
        list_labels = ["Introduction", "Methods", "Results", "Discussion"]
        for label in list_labels:
            session.run("""MATCH ()-[r:METAOCCUR_%s]->() DELETE r""" % (label.upper()))
            session.run("""MATCH ()-[r:METAOCCUR_%s_ALL]->() DELETE r"""% (label.upper()))
            print(f"MetaCitations for {label}")
            session.run("""
                LOAD CSV WITH HEADERS FROM "file:///MetaCitations_%s.csv" AS csv
                MATCH (t:InferedTool {name:csv.id1}),(p:Publication {id:csv.id2})
                CREATE (t)-[:METAOCCUR_%s {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p)
            """% (label, label.upper())) 
            session.run("""
                LOAD CSV WITH HEADERS FROM "file:///MetaCitations_%s.csv" AS csv
                MATCH (t:InferedTool {name:csv.id2}),(p:Publication {id:csv.id1})
                CREATE (t)-[:METAOCCUR_%s {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p)
            """% (label, label.upper())) 
            session.run("""
                LOAD CSV WITH HEADERS FROM "file:///MetaCitations_%s.csv" AS csv
                MATCH (t:InferedTool {name:csv.id1}),(t2:InferedTool {name:csv.id2})
                CREATE (t)-[:METAOCCUR_%s {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(t2)
            """ % (label, label.upper()))
            session.run("""
                LOAD CSV WITH HEADERS FROM "file:///MetaCitations_%s.csv" AS csv
                MATCH (p:Publication {id:csv.id1}),(p2:Publication {id:csv.id2})
                CREATE (p)-[:METAOCCUR_%s {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p2)
            """% (label, label.upper())) 
            # Make an edge that is the sum of all edges
            session.run("""
                match (t)-[m:METAOCCUR_%s]->(p)
                WITH t,p, collect(m) as co
                UNWIND co as c
                WITH t,p,sum(c.times) as sumo
                create (t)-[:METAOCCUR_%s_ALL {times: sumo}]->(p)
                """% (label.upper(), label.upper()))
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
        # Make an edge that is the sum of all edges
        session.run("""
            match (t)-[m:METAOCCUR]->(p)
            WITH t,p, collect(m) as co
            UNWIND co as c
            WITH t,p,sum(c.times) as sumo
            create (t)-[:METAOCCUR_ALL {times: sumo}]->(p)
            """)

if __name__ == '__main__':
    graph()
    print("--- %s seconds ---" % (time.time() - start_time))
