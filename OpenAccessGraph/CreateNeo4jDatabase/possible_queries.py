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
        # See percentage of top topics in the different communties
        session.run("""
            CALL {
                match (t:Keyword)<-[:TOPIC]-(n)-[h:HAS_COMMUNITY]->(c:Community)
                where c.from_section="All"
                with c.com_id as community, collect(t) as topic, count(t) as ct
                return community, topic, ct
            }
            with community, ct, topic
            unwind topic as untop
            with community,untop, count(untop) as num, ct
            order by num DESC
            with community, collect(untop)[0] as topTopic, max(num) as number_of_times, ct as totalTopics
            where number_of_times >1
            return community, topTopic,toFloat(number_of_times)/totalTopics as percentage, number_of_times, totalTopics
            order by percentage desc, number_of_times desc
            """)
        # Main topics of each graph
        session.run("""
            CALL {
                match (t:Keyword)<-[:TOPIC]-(n)
                with  collect(t) as topic, count(t) as ct
                return topic, ct
            }
            with ct, topic
            unwind topic as untop
            with untop, count(untop) as num, ct
            order by num DESC
            with untop, max(num) as number_of_times, ct as totalTopics
            where number_of_times >1
            return untop,toFloat(number_of_times)/totalTopics as percentage, number_of_times, totalTopics
            order by percentage desc, number_of_times desc
            """)
        # Jaccard index between most similar communities -All vs. Methods
        session.run("""
            match (n1)-[:HAS_COMMUNITY]->(c1:Community)
            where c1.from_section="All"
            with c1.com_id as com1, collect(id(n1)) as cid1
            where size(cid1)>5
            match (n2)-[:HAS_COMMUNITY]->(c2:Community)
            where c2.from_section="METHODS"
            with com1, cid1,c2.com_id as com2, collect(id(n2)) as cid2
            where size(cid2)>5
            RETURN com1 AS from,
                com2 AS to,
                gds.alpha.similarity.jaccard(cid1, cid2) AS similarity
            order by similarity desc
            """)


if __name__ == '__main__':
    stats_graph()
