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
        
        methods_relations = session.run("""
                MATCH (i:InferedTool)-[o:METAOCCUR_METHODS_ALL]-(p)
                RETURN i.name as fromname,i.community as community,o.times as times,p.name as toname,p.subtitle as tosub
                ORDER BY o.times DESC 
                LIMIT 100
        """)
        results_relations = session.run("""
                MATCH (i:InferedTool)-[o:METAOCCUR_RESULTS_ALL]-(p)
                RETURN i.name as fromname,i.community as community,o.times as times,p.name as toname,p.subtitle as tosub
                ORDER BY o.times DESC 
                LIMIT 100
        """)
        edges_file = open("SoLiTo/OpenAccessGraph/CreateNeo4jDatabase/edge_relations.txt", "w")
        edges_file.write(f"name\ttoname\ttimes\tcommunity\tSection\n")

        for i in methods_relations:
            name =i["fromname"]
            community = i["community"]
            times = i["times"]
            if i["toname"]:
                toname = i["toname"]
            if i["tosub"]:
                toname = i["tosub"]
            edges_file.write(f"{name}\t{toname}\t{times}\t{community}\tMethods\n")
        for i in results_relations:
            name =i["fromname"]
            community = i["community"]
            times = i["times"]
            if i["toname"]:
                toname = i["toname"]
            if i["tosub"]:
                toname = i["tosub"]
            edges_file.write(f"{name}\t{toname}\t{times}\t{community}\tResults\n")
        
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

            
            
            
                

            
            
            
        
                
            
            

if __name__ == '__main__':
    stats_graph()
