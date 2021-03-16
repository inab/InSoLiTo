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
        session.run("""
                MATCH (n)-[o:METAOCCUR]-(p1)
                WHERE 1992 <=o.year <=1993
                WITH n, p1, collect(o) as co
                unwind co as c
                with sum(c.times) as sumo, n,p1, co
                where sumo >20
                RETURN n, sumo,co, p1 Limit 10
                """
        print("Search keyword OR keyword")
        session.run("""
                MATCH (n)-[o:METAOCCUR]-(p1)
                WHERE 1992 <=o.year <=2020 and any(x IN n.keywords WHERE x IN ["Sequencing", "FASTA"])
                WITH n, p1, collect(o) as co
                unwind co as c
                with sum(c.times) as sumo, n,p1, co
                where sumo >20
                RETURN n,co,p1, sumo limit 10
            """)
        print("Return InteredTools relations and Publications relations")
        session.run("""
            match p=(i:InferedTool)-[m:METAOCCUR]-() 
            optional match q = (:Publication)-[o:METAOCCUR]-()
            where o.times >100
            return p, q limit 1000
            """)
        
############## Queries formatted for the HTML ####################################
        print("General query with limit 1000")
        session.run("""
            MATCH (i:InferedTool)-[o:METAOCCUR]-(p) WITH p,i, collect(o) as co unwind co as c with sum(c.times) as sumo, p,i, co RETURN i,co,p limit 1000
            """)
        print("Correct search keyword AND keyword")
        session.run("""
             MATCH (i:InferedTool)-[o:METAOCCUR]-(p) WHERE 'Sequence' in i.keywords and 'FASTA' in i.keywords WITH p,i, collect(o) as co unwind co as c with sum(c.times) as sumo, p,i, co RETURN i,co,p limit 1000
            """)
        print("Correct search keyword AND keyword + time period")
        session.run("""
            MATCH (i:InferedTool)-[o:METAOCCUR]-(p) WHERE 'Sequence' in i.keywords and 'FASTA' in i.keywords and 2000 <=o.year <=2010 WITH p,i, collect(o) as co unwind co as c with sum(c.times) as sumo, p,i, co RETURN i,co,p
            """)
        print("Correct search keyword or keyword + time")
        session.run("""
            MATCH (i:InferedTool)-[o:METAOCCUR]-(p) WHERE 'Sequence' in i.keywords or 'FASTA' in i.keywords and 2000 <=o.year <=2010 WITH p,i, collect(o) as co unwind co as c with sum(c.times) as sumo, p,i, co RETURN i,co,p
            """)
        print("Correct search keyword or keyword + time + more than 500 citations")
        session.run("""
            MATCH (i:InferedTool)-[o:METAOCCUR]-(p) WHERE 'Sequence' in i.keywords or 'FASTA' in i.keywords and 2000 <=o.year <=2010 WITH p,i, collect(o) as co unwind co as c with sum(c.times) as sumo, p,i, co where sumo >500 RETURN i,co,p
            """)
        # Command line
        print("Correct search keyword or keyword + time + more than 500 citations command line")
        session.run("""
            MATCH (i:InferedTool)-[o:METAOCCUR]-(p) WHERE 'Sequence' in i.keywords or 'FASTA' in i.keywords and 2000 <=o.year <=2010 WITH p,i, collect(o) as co unwind co as c with sum(c.times) as sumo, p,i, co where sumo >500 RETURN i,co,p
            """)

            

if __name__ == '__main__':
    stats_graph()
