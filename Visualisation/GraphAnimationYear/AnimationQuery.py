# Import libraries
from neo4j import GraphDatabase
import sys

# URL of the Neo4j Server
uri = "bolt://localhost:7687"
# Driver to connect to the Server with the author and the password
# To be able to use it, you need to open your neo4j server before
driver = GraphDatabase.driver(uri, auth=("neo4j", "1234"))

with driver.session() as session:

    tool_name = sys.argv[1] # Tool name
    n_first = sys.argv[2]   # Minimum co-occurrences in the first degree neighbours
    n_second = sys.argv[3]  # Minimum co-occurrences in the first degree neighbours
    year_edges = open(sys.argv[4], "w") # Name of the output file
    
    year_edges.write(f'"name_i"\t"name_p"\tpageRank_i\tcommunity_i\tpageRank_p\tcommunity_p\tyear\tyear_end\tweight\ttotal_weight\ttype_i\ttype_p\n')
    
    
    # Querying in Neo4j
    for year_query in range(1990, 2022):
        first_file_year= session.run("""
            CALL {
                MATCH (i:InferedTool)-[o:METAOCCUR]->(p) 
                WHERE i.name="%s" 
                WITH p,i, collect(o) as co 
                    UNWIND co as c 
                WITH sum(c.times) as sumo, p,i, co 
                WHERE sumo > %s 
                RETURN i,p,co, sumo 
                order by sumo DESC limit 100
            }
            WITH i,co,p, sumo 
                UNWIND co as c 
            WITH i,p,sumo,c 
            WHERE c.year = %s 
            RETURN i,p,sumo,c
        """%(tool_name,n_first, year_query))
        second_file_year= session.run("""
            CALL {
                MATCH (i:InferedTool)-[o:METAOCCUR_ALL]-(p) 
                where i.name="%s" and o.times >%s 
                with distinct i, o, p 
                ORDER BY o.times DESC limit 100
                match (p)-[o2:METAOCCUR]-(p2)
                WITH p,p2, collect(o2) as co 
                        UNWIND co as c 
                    WITH sum(c.times) as sumo, p,p2, co 
                    WHERE sumo > %s
                    RETURN p2,p,co, sumo 
            }
            WITH p2,co,p, sumo 
                UNWIND co as c 
            WITH p2,p,sumo,c 
            WHERE c.year = %s 
            RETURN p,p2,sumo,c
        """%(tool_name,n_first, n_second, year_query))
        
        # Write the first degree relationships in a file
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

        # Write the second degree relationships in a file
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

