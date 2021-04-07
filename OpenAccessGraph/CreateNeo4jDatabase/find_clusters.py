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
        clusters=session.run("""
                MATCH (i:InferedTool)-[o:METAOCCUR]-(p:InferedTool) WHERE "Proteomics" in i.topics and "Proteomics" in p.topics  WITH p,i, collect(o) as co unwind co as c with sum(c.times) as sumo, p,i, co where i.community = p.community and size(i.input_data)>0 and size(i.output_data)>0 and size(p.input_data)>0 and size(p.output_data)>0 and size(i.input_format)>0 and size(i.output_format)>0 and size(p.input_format)>0 and size(p.output_format)>0 and sumo>200 RETURN i.community, collect(distinct i.name) as coli, p.community, collect(distinct p.name) as colp
                """
                )
        for row in clusters:
            set_tools = set()
            if row["i.community"] == row["p.community"]:
                for tool in row["coli"]:
                    set_tools.add(tool)
                for tool in row["colp"]:
                    set_tools.add(tool)
                print(row["i.community"],row["p.community"],set_tools)

if __name__ == '__main__':
    stats_graph()
