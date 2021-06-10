# Import libraries
from neo4j import GraphDatabase

# URL of the Neo4j Server
uri = "bolt://localhost:7687"
# Driver to connect to the Server with the author and the password
# To be able to use it, you need to open your neo4j server before
driver = GraphDatabase.driver(uri, auth=("neo4j", "1234"))

def stats_graph():
    with driver.session() as session:
                
        ########## Edges file
        edges_file = open("SoLiTo/Meta_OA/edge_relations_all.txt", "w")
        edges_file.write(f"name_i\tname_p\tpageRank_i\tcommunity_i\tpageRank_p\tcommunity_p\tweight\tSection\n")
        
        list_labels = [["", "All"],["_INTRODUCTION", "Introduction"], ["_METHODS", "Methods"], ["_RESULTS", "Results"], ["_DISCUSSION", "Discussion"]]
        for label in list_labels:
            relations = session.run("""
                    MATCH (i:InferedTool)-[o:METAOCCUR%s_ALL]->(p) WITH p,i, collect(o) as co UNWIND co as c WITH sum(c.times) as sumo, p,i, co ORDER BY sumo DESC with distinct i limit 100 match (i)-[o:METAOCCUR%s_ALL]->(p) WITH p,i, collect(o) as co UNWIND co as c WITH sum(c.times) as sumo, p,i, co where sumo >=50
                    RETURN distinct i.name as name_i,i.community as community_i,i.pageRank as pageRank_i , sumo as weight,p.name as toname,p.subtitle as tosub, p.community as community_p,p.pageRank as pageRank_p
            """% (label[0], label[0]))

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
        
        ########## Edges file
        number_of_nodes = open("SoLiTo/Meta_OA/number_of_nodes_prot.txt", "w")
        number_of_nodes.write(f"Time\tTool\tPublication\tpercentage\tUsecase\n")
        
        for num_cor in range(10, 1000):
            percentage_tools = session.run("""
                Match (n:InferedTool)-[m:METAOCCUR_ALL]-()
                where m.times > %s
                with distinct n
                return count(n) as num_tools
            """ % (num_cor))
            
            percentage_publications = session.run("""
                Match (n:Publication)-[m:METAOCCUR_ALL]-()
                where m.times > %s
                with distinct n
                return count(n) as num_pubs
            """ % (num_cor))

            num_tools = percentage_tools.data()[0]["num_tools"]
            num_pubs = percentage_publications.data()[0]["num_pubs"]
            
            print(num_cor,num_tools, num_pubs,  num_tools/(num_tools + num_pubs))
            number_of_nodes.write(f"{num_cor}\t{num_tools}\t{num_pubs}\t{num_tools/(num_tools + num_pubs)}\t'Proteomics'\n")
        
        number_of_nodes.close()
        
        
        
        # Year with edges file
        
        year_edges = open("SoLiTo/Meta_OA/year_edges_trimal.txt", "w")
        year_edges.write(f'"name_i"\t"name_p"\tpageRank_i\tcommunity_i\tpageRank_p\tcommunity_p\tyear\tyear_end\tweight\ttotal_weight\ttype_i\ttype_p\n')
        
        for year_query in range(1998, 2022):
            first_file_year= session.run("""
                CALL {
                    MATCH (i:InferedTool)-[o:METAOCCUR]->(p) 
                    WHERE i.name="Trinity" 
                    WITH p,i, collect(o) as co 
                        UNWIND co as c 
                    WITH sum(c.times) as sumo, p,i, co 
                    WHERE sumo > 50 
                    RETURN i,p,co, sumo 
                    order by sumo DESC limit 100
                }
                WITH i,co,p, sumo 
                    UNWIND co as c 
                WITH i,p,sumo,c 
                WHERE c.year = %s 
                RETURN i,p,sumo,c
            """%(year_query))
            second_file_year= session.run("""
                CALL {
                    MATCH (i:InferedTool)-[o:METAOCCUR_ALL]-(p) 
                    where i.name="Trinity" and o.times >50 
                    with distinct i, o, p 
                    ORDER BY o.times DESC limit 100
                    match (p)-[o2:METAOCCUR]-(p2)
                    WITH p,p2, collect(o2) as co 
                            UNWIND co as c 
                        WITH sum(c.times) as sumo, p,p2, co 
                        WHERE sumo > 500
                        RETURN p2,p,co, sumo 
                }
                WITH p2,co,p, sumo 
                    UNWIND co as c 
                WITH p2,p,sumo,c 
                WHERE c.year = %s 
                RETURN p,p2,sumo,c
            """%(year_query))
            
            for row_query in first_file_year:
                node_i = row_query['i']
                node_p = row_query['p']
                edge = row_query['c']
                total_weight = row_query['sumo']

                # First node
                name_i = node_i["name"]
                pageRank_i = node_i["pageRank"]
                community_i = node_i["community"]
                type_i = "InferredTool"
                
                # Second node
                node_label = list(node_p.labels)
                if node_label[0] == "InferedTool":
                    name_p = node_p["name"]
                    pageRank_p = node_p["pageRank"]
                    community_p = node_p["community"]
                    type_p = "InferredTool"
                else:
                    name_p = node_p["title"]
                    pageRank_p = node_p["pageRank"]
                    community_p = node_p["community"]
                    type_p = "Publication"
                    
                # Edge
                year = edge["year"]
                year_end = 2021
                weight = edge["times"]
                
                # Write to file
                year_edges.write(f"{name_i}\t{name_p}\t{pageRank_i}\t{community_i}\t{pageRank_p}\t{community_p}\t{year}\t{year_end}\t{weight}\t{total_weight}\t{type_i}\t{type_p}\n")
                
            for row_query in second_file_year:
                node_p = row_query['p']
                node_p2 = row_query['p2']

                edge = row_query['c']
                total_weight = row_query['sumo']
                
                # First node
                node_label = list(node_p.labels)
                if node_label[0] == "InferedTool":
                    name_p = node_p["name"]
                    pageRank_p = node_p["pageRank"]
                    community_p = node_p["community"]
                    type_p = "InferredTool"
                else:
                    name_p = node_p["title"]
                    pageRank_p = node_p["pageRank"]
                    community_p = node_p["community"]
                    type_p = "Publication"
                
                # Second node
                node_label = list(node_p2.labels)
                if node_label[0] == "InferedTool":
                    name_p2 = node_p2["name"]
                    pageRank_p2 = node_p2["pageRank"]
                    community_p2 = node_p2["community"]
                    type_p2 = "InferredTool"
                else:
                    name_p2 = node_p2["title"]
                    pageRank_p2 = node_p2["pageRank"]
                    community_p2 = node_p2["community"]
                    type_p2 = "Publication"
                # Edge
                year = edge["year"]
                year_end = 2021
                weight = edge["times"]
                
                # Write to file
                year_edges.write(f"'{name_p}'\t'{name_p2}'\t{pageRank_p}\t{community_p}\t{pageRank_p2}\t{community_p2}\t{year}\t{year_end}\t{weight}\t{total_weight}\t{type_p}\t{type_p2}\n")

        year_edges.close()
        


if __name__ == '__main__':
    stats_graph()
