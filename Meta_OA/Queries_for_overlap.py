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
                
        ########## Edges file
        edges_file = open("SoLiTo/Meta_OA/edge_relations.txt", "w")
        edges_file.write(f"name_i\tname_p\tpageRank_i\tcommunity_i\tpageRank_p\tcommunity_p\tweight\tSection\n")
        
        list_labels = [["", "All"],["_INTRODUCTION", "Introduction"], ["_METHODS", "Methods"], ["_RESULTS", "Results"], ["_DISCUSSION", "Discussion"]]
        for label in list_labels:
            relations = session.run("""
                    MATCH (i:InferedTool)-[o:METAOCCUR%s_ALL]->(p)
                    RETURN i.name as name_i,i.community as community_i,i.pageRank as pageRank_i ,o.times as weight,p.name as toname,p.subtitle as tosub, p.community as community_p,p.pageRank as pageRank_p
                    ORDER BY o.times DESC 
                    LIMIT 100
            """% (label[0]))

            for i in relations:
                name_i =i["name_i"]
                if i["toname"]:
                    name_p = i["toname"]
                if i["tosub"]:
                    name_p = i["tosub"]
                pageRank_i = i["pageRank_i"]
                community_i = i["community_i"]
                pageRank_p = i["pageRank_p"]
                community_p = i["community_p"]
                weight = i["weight"]

                edges_file.write(f"{name_i}\t{name_p}\t{pageRank_i}\t{community_i}\t{pageRank_p}\t{community_p}\t{weight}\t{label[1]}\n")
        
        edges_file.close()
        
        # Year with edges file
        
        year_edges = open("SoLiTo/Meta_OA/year_edges.txt", "w")
        year_edges.write(f'"name_i"\t"name_p"\tpageRank_i\tcommunity_i\tpageRank_p\tcommunity_p\tyear\tyear_end\tweight\ttotal_weight\n')
        
        for year_query in range(2007, 2022):
            methods_file_year= session.run("""
            CALL{ MATCH (i:InferedTool)-[o:METAOCCUR]->(p) WITH p,i, collect(o) as co UNWIND co as c WITH sum(c.times) as sumo, p,i, co RETURN i,co,p,sumo ORDER BY sumo DESC LIMIT 100} WITH i,co,p, sumo UNWIND co as c WITH i,p,sumo,c WHERE c.year = %s RETURN i,p,sumo,c
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
