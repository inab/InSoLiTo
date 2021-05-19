# Import libraries
from neo4j import GraphDatabase
import networkx as nx
import matplotlib.pyplot as plt

from operator import itemgetter
from networkx.algorithms import community #This part of networkx, for community detection, needs to be imported separately.



# URL of the Neo4j Server
uri = "bolt://localhost:7687"
# Driver to connect to the Server with the author and the password
# To be able to use it, you need to open your neo4j server before
driver = GraphDatabase.driver(uri, auth=("neo4j", "1234"))

def create_networkx_graph():
    
    query = " MATCH (n)-[r]->(c) RETURN *"

    results = driver.session().run(query)

    G = nx.MultiDiGraph()

    nodes = list(results.graph()._nodes.values())
    for node in nodes:
        G.add_node(node.id, labels=list(node._labels)[0], properties=node._properties)

    rels = list(results.graph()._relationships.values())
    for rel in rels:
        G.add_edge(rel.start_node.id, rel.end_node.id, key=rel.id, type=rel.type, properties=rel._properties)
        


if __name__ == '__main__':
    create_networkx_graph()
