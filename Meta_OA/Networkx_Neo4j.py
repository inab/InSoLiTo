# Import libraries
from neo4j import GraphDatabase
import networkx as nx
import matplotlib.pyplot as plt

from operator import itemgetter
from networkx.algorithms import community #This part of networkx, for community detection, needs to be imported separately.

from cdlib import viz
from cdlib import algorithms



# URL of the Neo4j Server
uri = "bolt://localhost:7687"
# Driver to connect to the Server with the author and the password
# To be able to use it, you need to open your neo4j server before
driver = GraphDatabase.driver(uri, auth=("neo4j", "1234"))

#def create_networkx_graph():
    
query = "MATCH (n)-[q:METAOCCUR_ALL]-(a) RETURN *"

results = driver.session().run(query)

G = nx.Graph()

nodes = list(results.graph()._nodes.values())
for node in nodes:
    G.add_node(node.id, labels=list(node._labels)[0], properties=node._properties)


rels = list(results.graph()._relationships.values())
for rel in rels:
    G.add_edge(rel.start_node.id, rel.end_node.id, weight =rel._properties['times'], key=rel.id, type=rel.type, properties=rel._properties)

d={}
for i,q in G.nodes(data=True): 
    if q['properties']['community'] not in d:
        d[q['properties']['community']]=[i]
    else:
        if i not in d[q['properties']['community']]:
            d[q['properties']['community']] = d[q['properties']['community']] + [i]

            
coms = algorithms.louvain(G, weight='times', randomize = 1)

coms_graph = []
for key, value in d.items():
    coms_graph.append(value)

count_louvain=0
l = []
for i in coms.communities:
    l.append(i)
    for j in coms_graph:
        if i==j:
            count_louvain+=1
            l.remove(i)
print("Equal community:",count_louvain)
print("#total communtites in louvain:", len(coms.communities))            
print("#total communtites in gra:", len(coms_graph))            
            
coms_leiden = algorithms.leiden(G, weights='weight')

count_leiden=0
l = []
for i in coms_leiden.communities:
    l.append(i)
    for j in coms_graph:
        if i==j:
            count_leiden+=1
            l.remove(i)

print("Equal community:",count_leiden)
print("#total communtites in leiden:", len(coms_leiden.communities))      
print("#total communtites in graph:", len(coms_graph))


# Subset 
import numpy as np
F = nx.Graph()
for (u, v, wt) in G.edges.data('weight'):
    if wt >500:
        print(u,v,wt)
        if u not in F.nodes():
            F.add_node(u, labels = G.nodes()[u]['labels'],
                        properties = G.nodes()[u]['properties'])
        if v not in F.nodes():
            F.add_node(v, labels = G.nodes()[v]['labels'],
                        properties = G.nodes()[v]['properties'])
        F.add_edge(u,v,weight=wt)
        

pos = nx.spring_layout(F, k=10/np.sqrt(len(F.nodes())), iterations=20)
viz.plot_network_clusters(F, coms, pos, plot_labels = True, node_size = 400)

#if __name__ == '__main__':
    #create_networkx_graph()`
