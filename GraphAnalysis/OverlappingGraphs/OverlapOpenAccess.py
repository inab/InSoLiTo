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
        
        ########## Edges file OpenAccess database
        edges_file = open(sys.argv[1], "w")
        min_coocurrences = sys.argv[2]

        edges_file.write(f"name_i\tname_p\tpageRank_i\tcommunity_i\tpageRank_p\tcommunity_p\tweight\tSection\n")
        
        list_labels = [["", "All"],["_INTRODUCTION", "Introduction"], ["_METHODS", "Methods"], ["_RESULTS", "Results"], ["_DISCUSSION", "Discussion"]]
        for label in list_labels:
            relations = session.run("""
                    MATCH (i:InferedTool)-[o:METAOCCUR%s_ALL]->(p) WITH p,i, collect(o) as co UNWIND co as c WITH sum(c.times) as sumo, p,i, co ORDER BY sumo DESC with distinct i limit 100 match (i)-[o:METAOCCUR%s_ALL]->(p) WITH p,i, collect(o) as co UNWIND co as c WITH sum(c.times) as sumo, p,i, co where sumo >=%s
                    RETURN distinct i.name as name_i,i.community as community_i,i.pageRank as pageRank_i , sumo as weight,p.name as toname,p.subtitle as tosub, p.community as community_p,p.pageRank as pageRank_p
            """% (label[0], label[0], min_coocurrences))

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

if __name__ == '__main__':
    stats_graph()
