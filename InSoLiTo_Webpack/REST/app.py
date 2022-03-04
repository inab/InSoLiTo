from flask import Flask, Response, render_template, request
import json
from wtforms import TextField, Form
from neo4j import GraphDatabase
import math


# URL of the Neo4j Server
uri = "bolt://localhost:7687"
# Driver to connect to the Server with the author and the password
# To be able to use it, you need to open your neo4j server before
driver = GraphDatabase.driver(uri, auth=("neo4j", "1234"))
 
app = Flask(__name__, template_folder=".")


def logslider(position, minv, maxv):
    #position between 0 and 100
    minp = 0
    maxp = 100
    
    # Results between 11 and Max occurrences in database
    minv= math.log(minv)
    maxv= math.log(maxv)
    
    # Scale the values
    scale = (maxv-minv) / (maxp-minp)
    
    value = math.trunc(math.exp(minv + scale*(position-minp)))
    
    return value

 
def CreateToolsTopicsList():
    with driver.session() as session:
        tools_graph = session.run("""
                match (n:InferedTool), (d:Database)
                with collect(n) as cn, collect(d) as cd
                with cn+cd as tools_nodes
                unwind tools_nodes as tools
                return distinct tools.name as name, id(tools) as id, labels(tools) as label
            """)
        
        topics_graph = session.run("""
            match ()-[m:METAOCCUR_ALL]-(n)-[:TOPIC]->(k:Keyword)-[:SUBCLASS*]->(k2:Keyword)
            where m.times>10
            with distinct n, k
            with collect(id(n)) as cn, k
            return cn, k.label as name
        """)
        tools = [{"value":tool["name"], "identificator":tool["id"], "labelnode":tool["label"]} for tool in tools_graph]
        topics = [{"value":topic["name"], "identificator":topic["cn"], "labelnode":"Topic"} for topic in topics_graph]
        
        count_relationships = session.run("""
            match ()-[m:METAOCCUR_ALL]->()
            return m.times as times, count(m.times) as ctimes
            order by m.times
            """)
        minv = 1000000
        maxv = 0
        relations_all = {}
        for relationships in count_relationships:
            if relationships["times"]< minv:
                minv = relationships["times"]
            if relationships["times"]> maxv:
                maxv = relationships["times"]
            relations_all[relationships["times"]]=math.log(relationships["ctimes"])

        relations_log = {}
        for i in range(101):
            value = logslider(i, minv,maxv)
            if value in relations_all:
                relations_log[value]=relations_all[value]
            else:
                res = relations_all.get(value) or min(relations_all.keys(), key = lambda key: abs(key-value))
                relations_log[res] = relations_all[res]
            
        
        topics_and_tools= topics + tools
    return json.dumps(topics_and_tools), json.dumps(relations_log)
 
 
@app.route('/')
def index():
    tool_topic, relations = CreateToolsTopicsList()
    return render_template("static/index-test.html", tool_topic=tool_topic, relations = relations)
 
if __name__ == '__main__':
    app.run(debug=True)
