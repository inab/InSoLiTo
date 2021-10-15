

def citations_edges(driver):
    with driver.session() as session:
        session.run("""MATCH ()-[r:METAOCCUR]->() DELETE r""")
        session.run("""MATCH ()-[r:METAOCCUR_ALL]->() DELETE r""")


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
        print("InferedTool-InferedTool citations")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///MetaCitations.csv" AS csv
            MATCH (t:InferedTool {name:csv.id1}),(t2:InferedTool {name:csv.id2})
            CREATE (t)-[:METAOCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(t2)
        """)
        print("Publication-Publication citations")
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

