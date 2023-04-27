

def citations_edges(driver, Metacitations_file, Metacitations_file_N1, Metacitations_file_N2):
    with driver.session() as session:
        session.run("""MATCH ()-[r:METAOCCUR]->() DELETE r""")
        session.run("""MATCH ()-[r:METAOCCUR_ALL]->() DELETE r""")

        # Relationships N1+N2

        print("Tool-Publication citations")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            MATCH (t:Tool {label:csv.id1}),(p:Publication {pmid:csv.id2})
            CREATE (t)-[:METAOCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p)
        """ % Metacitations_file)
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            MATCH (t:Tool {label:csv.id2}),(p:Publication {pmid:csv.id1})
            CREATE (t)-[:METAOCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p)
        """ % Metacitations_file)

        print("Tool-Tool citations")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            MATCH (t:Tool {label:csv.id1}),(t2:Tool {label:csv.id2})
            CREATE (t)-[:METAOCCUR {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(t2)
        """ % Metacitations_file)
        
        # Make an edge that is the sum of all edges
        session.run("""
            match (t)-[m:METAOCCUR]->(p)
            WITH t,p, collect(m) as co
            UNWIND co as c
            WITH t,p,sum(c.times) as sumo
            create (t)-[:METAOCCUR_ALL {times: sumo}]->(p)
            """)
        
        # Relationships N1

        print("Tool-Publication citations")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            MATCH (t:Tool {label:csv.id1}),(p:Publication {pmid:csv.id2})
            CREATE (t)-[:METAOCCUR_N1 {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p)
        """ % Metacitations_file_N1)
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            MATCH (t:Tool {label:csv.id2}),(p:Publication {pmid:csv.id1})
            CREATE (t)-[:METAOCCUR_N1 {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p)
        """ % Metacitations_file_N1)

        print("Tool-Tool citations")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            MATCH (t:Tool {label:csv.id1}),(t2:Tool {label:csv.id2})
            CREATE (t)-[:METAOCCUR_N1 {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(t2)
        """ % Metacitations_file_N1)
        
        # Make an edge that is the sum of all edges
        session.run("""
            match (t)-[m:METAOCCUR_N1]->(p)
            WITH t,p, collect(m) as co
            UNWIND co as c
            WITH t,p,sum(c.times) as sumo
            create (t)-[:METAOCCUR_N1_ALL {times: sumo}]->(p)
            """)

        # Relationships N2

        print("Tool-Publication citations")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            MATCH (t:Tool {label:csv.id1}),(p:Publication {pmid:csv.id2})
            CREATE (t)-[:METAOCCUR_N2 {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p)
        """ % Metacitations_file_N2)
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            MATCH (t:Tool {label:csv.id2}),(p:Publication {pmid:csv.id1})
            CREATE (t)-[:METAOCCUR_N2 {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(p)
        """ % Metacitations_file_N2)

        print("Tool-Tool citations")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            MATCH (t:Tool {label:csv.id1}),(t2:Tool {label:csv.id2})
            CREATE (t)-[:METAOCCUR_N2 {times:toInteger(csv.n_citations), year:toInteger(csv.year)}]->(t2)
        """ % Metacitations_file_N2)
        
        # Make an edge that is the sum of all edges
        session.run("""
            match (t)-[m:METAOCCUR_N2]->(p)
            WITH t,p, collect(m) as co
            UNWIND co as c
            WITH t,p,sum(c.times) as sumo
            create (t)-[:METAOCCUR_N2_ALL {times: sumo}]->(p)
            """)
