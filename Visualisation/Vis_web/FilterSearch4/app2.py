from flask import Flask, Response, render_template, request
import json
from wtforms import TextField, Form
from neo4j import GraphDatabase


# URL of the Neo4j Server
uri = "bolt://localhost:7687"
# Driver to connect to the Server with the author and the password
# To be able to use it, you need to open your neo4j server before
driver = GraphDatabase.driver(uri, auth=("neo4j", "1234"))
 
app = Flask(__name__)
 
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
            match (k:Keyword)
            where (k)<-[:TOPIC]-() or (k)-[:SUBCLASS{type:"topic"}]-()
            return distinct k.label as name, id(k) as id
        """)

        tools = [{"value":tool["name"], "identificator":tool["id"], "labelnode":tool["label"]} for tool in tools_graph]
        topics = [{"value":topic["name"], "identificator":topic["id"], "labelnode":"Topic"} for topic in topics_graph]
        

        #topics = [topic for topic in topics_graph]

        #topics_and_tools= topics + tools
        #print(tools)

        #topics = [topic["label"].replace("_", " ") for topic in topics_graph]
        topics_and_tools= topics + tools
    return json.dumps(topics_and_tools)
 
 
@app.route('/')
def index():
    tool_topic = CreateToolsTopicsList()
    return render_template("algo_100_best_2_1.html", tool_topic=tool_topic)
 
if __name__ == '__main__':
    app.run(debug=True)
