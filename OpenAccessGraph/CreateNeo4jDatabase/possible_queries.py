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
        # Overlapping communities between Methods and Results
        session.run("""
            match (i)-[:HAS_COMMUNITY]->(top)
            where top.from_section="RESULTS" OR top.from_section="METHODS"
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
