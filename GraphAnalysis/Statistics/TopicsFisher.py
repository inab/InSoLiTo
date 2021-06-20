# Import libraries
from neo4j import GraphDatabase
import sys

# URL of the Neo4j Server
uri = "bolt://localhost:7687"
# Driver to connect to the Server with the author and the password
# To be able to use it, you need to open your neo4j server before
driver = GraphDatabase.driver(uri, auth=("neo4j", "1234"))

def stats_graph():
    with driver.session() as session:
        
        # Topics for graph and communitites - For calculating the Fisher test
        # Top topics by community
        topics_comm = open(sys.argv[1], "w")
        topics_comm.write(f"topic\tpercentage\tntimes\ttotal\n")
        topics_community = session.run("""
            CALL {
                 MATCH (n:Community)-[h:METAOCCUR_COMM]-(q:Community)
                with n, collect(h) as ch
                where size(ch) >1
                with collect(n) as cn
                unwind cn as c
                with c
                match (t:Keyword)<-[:TOPIC]-(n)-[h:HAS_COMMUNITY]->(c)
                with c.com_id as community, collect(t) as topic, count(t) as ct
                return community, topic, ct
            }
            with community, ct, topic
            unwind topic as untop
            with community,untop, count(untop) as num, ct
            order by num DESC
            with community, collect(untop)[0] as topTopic, max(num) as number_of_times, ct as totalTopics
            where number_of_times >1
            return community, topTopic.label as topic,toFloat(number_of_times)/totalTopics as percentage, number_of_times, totalTopics
            order by number_of_times desc, number_of_times desc
        """)
        
        for row_comm in topics_community:
            community = row_comm["community"]
            topic = row_comm["topic"]
            percentage = row_comm["percentage"]
            ntimes = row_comm["number_of_times"]
            total = row_comm["totalTopics"]
            topics_comm.write(f"{community}\t{topic}\t{percentage}\t{ntimes}\t{total}\n")
        topics_comm.close()

        
        
        # Top topics by graph
        topics_graph = open(sys.argv[2], "w")
        topics_graph.write(f"topic\tpercentage\tntimes\ttotal\n")
        
        main_topics_graph = session.run("""
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
            return untop.label as topic,toFloat(number_of_times)/totalTopics as percentage, number_of_times, totalTopics
            order by percentage desc, number_of_times desc
        """)
        
        for row_comm in main_topics_graph:
            topic = row_comm["topic"]
            percentage = row_comm["percentage"]
            ntimes = row_comm["number_of_times"]
            total = row_comm["totalTopics"]
            topics_graph.write(f"{topic}\t{percentage}\t{ntimes}\t{total}\n")
        topics_graph.close()


if __name__ == '__main__':
    stats_graph()
