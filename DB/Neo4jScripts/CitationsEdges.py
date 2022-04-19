

def citations_edges(driver, file_path, Metacitations_file):
    with driver.session() as session:
        session.run("""MATCH ()-[r:METAOCCUR]->() DELETE r""")
        session.run("""MATCH ()-[r:METAOCCUR_ALL]->() DELETE r""")


        print("Tool-Publication citations")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s%s" AS csv
            MATCH (t:Tool {name:csv.id1}),(p:Publication {pmid:csv.id2})
            CREATE (t)-[:METAOCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p)
        """ % (file_path, Metacitations_file))
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s%s" AS csv
            MATCH (t:Tool {name:csv.id2}),(p:Publication {pmid:csv.id1})
            CREATE (t)-[:METAOCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p)
        """ % (file_path, Metacitations_file))
        print("Tool-Tool citations")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s%s" AS csv
            MATCH (t:Tool {name:csv.id1}),(t2:Tool {name:csv.id2})
            CREATE (t)-[:METAOCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(t2)
        """ % (file_path, Metacitations_file))
        print("Publication-Publication citations")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s%s" AS csv
            MATCH (p:Publication {pmid:csv.id1}),(p2:Publication {pmid:csv.id2})
            CREATE (p)-[:METAOCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p2)
        """ % (file_path, Metacitations_file))
        # Make an edge that is the sum of all edges
        session.run("""
            match (t)-[m:METAOCCUR]->(p)
            WITH t,p, collect(m) as co
            UNWIND co as c
            WITH t,p,sum(c.times) as sumo
            create (t)-[:METAOCCUR_ALL {times: sumo}]->(p)
            """)

