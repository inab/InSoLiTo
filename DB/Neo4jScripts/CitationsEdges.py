

def citations_edges(driver, Metacitations_file):
    with driver.session() as session:
        session.run("""MATCH ()-[r:METAOCCUR]->() DELETE r""")
        session.run("""MATCH ()-[r:METAOCCUR_ALL]->() DELETE r""")


        print("Tool-Publication citations")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            MATCH (t:Tool {label:csv.id1}),(p:Publication {pmid:csv.id2})
            CREATE (t)-[:METAOCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p)
        """ % (Metacitations_file))
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            MATCH (t:Tool {label:csv.id2}),(p:Publication {pmid:csv.id1})
            CREATE (t)-[:METAOCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p)
        """ % (Metacitations_file))
        print("Tool-Tool citations")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            MATCH (t:Tool {label:csv.id1}),(t2:Tool {label:csv.id2})
            CREATE (t)-[:METAOCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(t2)
        """ % (Metacitations_file))
        
        # Make an edge that is the sum of all edges
        session.run("""
            match (t)-[m:METAOCCUR]->(p)
            WITH t,p, collect(m) as co
            UNWIND co as c
            WITH t,p,sum(c.times) as sumo
            create (t)-[:METAOCCUR_ALL {times: sumo}]->(p)
            """)

