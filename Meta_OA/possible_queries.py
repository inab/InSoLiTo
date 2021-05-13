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
            MATCH (i:InferedTool)-[o:METAOCCUR]-(p) WHERE "Sequence analysis" in i.topics and "Sequence analysis" in p.topics and 2000 <=o.year <=2010 WITH p,i, collect(o) as co unwind co as c with sum(c.times) as sumo, p,i, co where sumo >500 RETURN i,co,p
            """)
        # Command line
        print("Correct search keyword or keyword + time + more than 500 citations command line")
        session.run("""
           MATCH (i:InferedTool)-[o:METAOCCUR]-(p) WHERE "Sequence analysis" in i.topics and "Sequence analysis" in p.topics  WITH p,i, collect(o) as co unwind co as c with sum(c.times) as sumo, p,i, co RETURN i.community, collect(Distinct i.name), p.community, collect(DISTINCT p.name)
            """)
        session.run("""
            CALL{
                MATCH (i:InferedTool)-[o:METAOCCUR]-(p)
                WITH p,i, collect(o) as co 
                    UNWIND co as c WITH sum(c.times) as sumo, p,i, co 
                RETURN i,co,p,sumo 
                ORDER BY sumo DESC 
                LIMIT 100
                }
            WITH i,co,p, sumo
                UNWIND co as c
            WITH i,p,sumo,c
            WHERE c.year = 2008
            RETURN i,p,sumo,c
            """)
        # Overlapping topics. See which ones are subtopics of other topics
        # It can be used for all type of edges
        session.run("""
            match (i:InferedTool)-[:TOPIC]->(top)
            with {item:id(top), categories:collect(id(i))} AS userData
            with collect(userData) as data
            CALL gds.alpha.similarity.overlap.stream({data: data})
            YIELD item1, item2, count1, count2, intersection, similarity
            RETURN gds.util.asNode(item1).label AS from, gds.util.asNode(item2).label AS to,
                count1, count2, intersection, similarity
            ORDER BY similarity DESC
            """)
        # Overlapping communities between Methods and Results with co-occurrences > 10
        session.run("""
            match ()-[mm]-(i)-[:HAS_COMMUNITY]->(top)
            where (type(mm) = "METAOCCUR_RESULTS_ALL" or type(mm) = "METAOCCUR_METHODS_ALL") and  mm.times > 10
            with {item:id(top), categories:collect(id(i))} AS userData
            with collect(userData) as data
            CALL gds.alpha.similarity.overlap.stream({data: data})
            YIELD item1, item2, count1, count2, intersection, similarity
            with gds.util.asNode(item1).com_id AS from, gds.util.asNode(item1).from_section AS section1, gds.util.asNode(item2).com_id AS to,
            gds.util.asNode(item2).from_section AS section2,
                count1, count2, intersection, similarity
            where section1 <>section2 and count1 > 1
            RETURN distinct from,section1,to, section2,
                count1, count2, intersection, similarity
            ORDER BY intersection DESC, similarity DESC
            """)
        # Add languages to the communities
        session.run("""
            match (l:Language)<-[:USE_LANGUAGE]-(i:InferedTool)-[:HAS_COMMUNITY]->(c:Community)
            where c.from_section="All"
            with c,l,count(i) as counti
            order by counti DESC
            with c,collect(l)[0] as mlanguage, max(counti) as maxcount
            set c.mlanguage=mlanguage.name, c.clanguage=id(mlanguage)
            return c,mlanguage, maxcount
            """)
        # Visualize communitites with languages
        session.run("""
            match (c1:Community)-[q:METAOCCUR_COMM]->(c2:Community)
            where c1.from_section="All" and c2.from_section="All" and (c1)<-[:HAS_COMMUNITY]-(:InferedTool)-[:USE_LANGUAGE]->(:Language) and (c2)<-[:HAS_COMMUNITY]-(:InferedTool)-[:USE_LANGUAGE]->(:Language)
            return c1,q,c2
            """)
        # Add topics to the communities
        session.run("""
            match (l:Keyword)<-[:TOPIC]-(i:InferedTool)-[:HAS_COMMUNITY]->(c:Community)
            where c.from_section="All"
            with c,l,count(i) as counti
            order by counti DESC
            with c,collect(l)[0] as mlanguage, max(counti) as maxcount
            set c.mtopic=mlanguage.label, c.ctopic=id(mlanguage)
            return c,mlanguage, maxcount
            """)
        # Visualize the topics of the communities
        session.run("""
            match (c1:Community)-[q:METAOCCUR_COMM]->(c2:Community)
            where c1.from_section="All" and c2.from_section="All" and (c1)<-[:HAS_COMMUNITY]-(:InferedTool)-[:TOPIC]->(:Keyword) and (c2)<-[:HAS_COMMUNITY]-(:InferedTool)-[:TOPIC]->(:Keyword)
            return c1,q,c2
            """)
        # Take 100 best nodes and show the relations between them
        session.run("""
             MATCH (i:InferedTool)-[o:METAOCCUR_ALL]->(p) WITH p,i, collect(o) as co UNWIND co as c WITH sum(c.times) as sumo, p,i, co ORDER BY sumo DESC with distinct i limit 100
            with collect(i) as ci
            unwind ci as i1
            unwind ci as i2
            match (i1)-[o:METAOCCUR_ALL]->(i2) WITH i1,i2, collect(o) as co UNWIND co as c WITH sum(c.times) as sumo, i1,i2, co return distinct i1, co, i2
            """)
        # Take 100 best nodes and extract all its relations with >50 co-occurrences
        session.run("""
            CALL{ MATCH (i:InferedTool)-[o:METAOCCUR]->(p) WITH p,i, collect(o) as co UNWIND co as c WITH sum(c.times) as sumo, p,i, co ORDER BY sumo DESC with distinct i limit 100 match (i)-[o:METAOCCUR]->(p) WITH p,i, collect(o) as co UNWIND co as c WITH sum(c.times) as sumo, p,i, co where sumo >=50 return distinct i,p,co, sumo } WITH i,co,p, sumo UNWIND co as c WITH i,p,sumo,c WHERE c.year = 2006 RETURN i,p,sumo,c
            """)

if __name__ == '__main__':
    stats_graph()
