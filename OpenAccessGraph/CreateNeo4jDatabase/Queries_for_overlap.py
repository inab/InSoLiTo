# Import libraries
from neo4j import GraphDatabase
import itertools
import sys
import json

# URL of the Neo4j Server
uri = "bolt://localhost:7687"
# Driver to connect to the Server with the author and the password
# To be able to use it, you need to open your neo4j server before
driver = GraphDatabase.driver(uri, auth=("neo4j", "1234"))

def stats_graph():
    with driver.session() as session:
        
        # Communities overlap file
        overlapping_nodes = session.run("""
            match ()-[mm]-(i)-[h:HAS_COMMUNITY]->(top)
            where (type(mm) = "METAOCCUR_RESULTS_ALL" or type(mm) = "METAOCCUR_METHODS_ALL") and  mm.times > 10
            return distinct i.name as name, i.subtitle as subtitle,top.com_id as com_id,top.from_section as section
        """)
        overlapping_file = open("SoLiTo/OpenAccessGraph/CreateNeo4jDatabase/overlapping_file.txt", "w")
        overlapping_file.write(f"name\tcom_id\tsection\n")

        for i in overlapping_nodes:
            if i["name"]:
                name =i["name"]
            if i["subtitle"]:
                name = i["subtitle"]
            com_id = i["com_id"]
            section = i["section"]
            overlapping_file.write(f"{name}\t{com_id}\t{section}\n")
        overlapping_file.close()
        
        ########## Edges file
        edges_file = open("SoLiTo/OpenAccessGraph/CreateNeo4jDatabase/edge_relations_all.txt", "w")
        edges_file.write(f"Name\tToname\tFromtype\tTotype\tTimes\tSection\tUseCase\n")
        
        type_relationship=[""]
        name_section= ["All"]
        
        for i in range(len(type_relationship)):
            relations_query = session.run("""
                    MATCH (i)-[o:METAOCCUR%s_ALL]->(p)
                    where o.times >100
                    RETURN i.name as fromname,i.title as fromtitle,o.times as times,p.name as toname,p.title as totitle
                """%(type_relationship[i]))

            for j in relations_query:
                if j["fromname"]:
                    fromtype = "Tool"
                    fromname = j["fromname"]
                if j["fromtitle"]:
                    fromtype = "Publication"
                    fromname = j["fromtitle"]
                times = j["times"]
                if j["toname"]:
                    totype = "Tool"
                    toname = j["toname"]
                if j["totitle"]:
                    totype = "Publication"
                    toname = j["totitle"]
                edges_file.write(f"{fromname}\t{toname}\t{fromtype}\t{totype}\t{times}\t{name_section[i]}\tAll\n")
        edges_file.close()
        
        
        # Year with edges file
        
        year_edges = open("SoLiTo/OpenAccessGraph/CreateNeo4jDatabase/year_edges.txt", "w")
        year_edges.write(f"name_i\tname_p\tpageRank_i\tcommunity_i\tpageRank_p\tcommunity_p\tyear\tyear_end\tweight\ttotal_weight\n")
        
        for year_query in range(2007, 2022):
            methods_file_year= session.run("""
            CALL{ MATCH (i:InferedTool)-[o:METAOCCUR_METHODS]->(p) WITH p,i, collect(o) as co UNWIND co as c WITH sum(c.times) as sumo, p,i, co RETURN i,co,p,sumo ORDER BY sumo DESC LIMIT 100} WITH i,co,p, sumo UNWIND co as c WITH i,p,sumo,c WHERE c.year = %s RETURN i,p,sumo,c
            """%(year_query))
            
            for row_query in methods_file_year:
                node_i = row_query['i']
                node_p = row_query['p']
                edge = row_query['c']
                total_weight = row_query['sumo']

                # First node
                name_i = node_i["name"]
                pageRank_i = node_i["pageRank"]
                community_i = node_i["community"]
                
                # Second node
                node_label = list(node_p.labels)
                if node_label[0] == "InferedTool":
                    name_p = node_p["name"]
                    pageRank_p = node_p["pageRank"]
                    community_p = node_p["community"]
                else:
                    name_p = node_p["subtitle"]
                    pageRank_p = node_p["pageRank"]
                    community_p = node_p["community"]
                    
                # Edge
                year = edge["year"]
                year_end = 2021
                weight = edge["times"]
                
                # Write to file
                year_edges.write(f"{name_i}\t{name_p}\t{pageRank_i}\t{community_i}\t{pageRank_p}\t{community_p}\t{year}\t{year_end}\t{weight}\t{total_weight}\n")
        year_edges.close()
        
        # Topics for graph and communitites - For calculating the Fisher test
        # Top topics by community
        topics_comm = open("SoLiTo/OpenAccessGraph/CreateNeo4jDatabase/topics_comm_prot.txt", "w")
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
        topics_graph = open("SoLiTo/OpenAccessGraph/CreateNeo4jDatabase/topics_graph_prot.txt", "w")
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
