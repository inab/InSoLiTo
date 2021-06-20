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
    list_labels = ["Introduction", "Methods", "Results", "Discussion"]
    for label in list_labels:
        with driver.session() as session:
            session.run("""MATCH ()-[r:METAOCCUR_%s]->() DELETE r""" % (label.upper()))
            session.run("""MATCH ()-[r:METAOCCUR_%s_ALL]->() DELETE r"""% (label.upper()))
            print(f"MetaCitations for {label}")
            print("Tool - Publication")
            session.run("""
                LOAD CSV WITH HEADERS FROM "file:///Citations_%s.csv" AS csv
                MATCH (t:InferedTool {name:csv.id1}),(p:Publication {id:csv.id2})
                CREATE (t)-[:METAOCCUR_%s {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p)
            """% (label, label.upper())) 
            print("Publication - Tool")
            session.run("""
                LOAD CSV WITH HEADERS FROM "file:///Citations_%s.csv" AS csv
                MATCH (t:InferedTool {name:csv.id2}),(p:Publication {id:csv.id1})
                CREATE (t)-[:METAOCCUR_%s {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p)
            """% (label, label.upper()))
            print("Tool - Tool")
            session.run("""
                LOAD CSV WITH HEADERS FROM "file:///Citations_%s.csv" AS csv
                MATCH (t:InferedTool {name:csv.id1}),(t2:InferedTool {name:csv.id2})
                CREATE (t)-[:METAOCCUR_%s {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(t2)
            """ % (label, label.upper()))
            print("Publication - Publication")
            session.run("""
                LOAD CSV WITH HEADERS FROM "file:///Citations_%s.csv" AS csv
                MATCH (p:Publication {id:csv.id1}),(p2:Publication {id:csv.id2})
                CREATE (p)-[:METAOCCUR_%s {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p2)
            """% (label, label.upper()))
            print("Metaoccur ALL")
            # Make an edge that is the sum of all edges
            session.run("""
                match (t)-[m:METAOCCUR_%s]->(p)
                WITH t,p, collect(m) as co
                UNWIND co as c
                WITH t,p,sum(c.times) as sumo
                create (t)-[:METAOCCUR_%s_ALL {times: sumo}]->(p)
                """% (label.upper(), label.upper()))
    with driver.session() as session:
        print("InferedTool-Publication citations")
        session.run("""MATCH ()-[r:METAOCCUR]->() DELETE r""")
        session.run("""MATCH ()-[r:METAOCCUR_ALL]->() DELETE r""")
        print("Tool - Publication")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Citations.csv" AS csv
            MATCH (t:InferedTool {name:csv.id1}),(p:Publication {id:csv.id2})
            CREATE (t)-[:METAOCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p)
        """)
        print("Publication - Tool")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Citations.csv" AS csv
            MATCH (t:InferedTool {name:csv.id2}),(p:Publication {id:csv.id1})
            CREATE (t)-[:METAOCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p)
        """)
        print("Tool - Tool")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Citations.csv" AS csv
            MATCH (t:InferedTool {name:csv.id1}),(t2:InferedTool {name:csv.id2})
            CREATE (t)-[:METAOCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(t2)
        """)
        print("Publication - Publication")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Citations.csv" AS csv
            MATCH (p:Publication {id:csv.id1}),(p2:Publication {id:csv.id2})
            CREATE (p)-[:METAOCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p2)
        """)
        print("Metaoccur ALL")
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
