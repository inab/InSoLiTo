

def citations_edges(driver, Metacitations_file):
    """
    Delete all edges METAOCCUR and METAOCCUR_ALL from the graph.
    Create new edges METAOCCUR and METAOCCUR_ALL with the data from the csv file.
    The csv file must contain the columns id1, id2, n_citations and year.
    The edges are created from the node id1 to the node id2 with the properties
    times and year.
    After creating all the edges METAOCCUR, a new edge METAOCCUR_ALL is created
    from each node to all the nodes that have an edge METAOCCUR with it.
    The property times of the edge METAOCCUR_ALL is the sum of all the properties
    times of the edges METAOCCUR.
    """
    with driver.session() as session:
        session.run("""MATCH ()-[r:METAOCCUR]->() DELETE r""")
        session.run("""MATCH ()-[r:METAOCCUR_ALL]->() DELETE r""")

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