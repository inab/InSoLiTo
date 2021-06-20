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
        
        ########## Edges file Metadata database
        edges_file = open(sys.argv[1], "w")
        min_coocurrences = sys.argv[2]
        edges_file.write(f"Name\tToname\tFromtype\tTotype\tTimes\tSection\tUseCase\n")
        
        relations_query = session.run(f"""
                MATCH (i)-[o:METAOCCUR_ALL]->(p)
                where o.times > {min_coocurrences}
                RETURN i.name as fromname,i.title as fromtitle,o.times as times,p.name as toname,p.title as totitle
            """)

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

if __name__ == '__main__':
    stats_graph()
