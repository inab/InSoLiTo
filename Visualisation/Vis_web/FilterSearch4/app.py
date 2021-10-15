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
 
class SearchTool(Form):
    autocomp = TextField('Insert Tool', id='tool_autocomplete')
 
 
@app.route('/_autocomplete', methods=['GET'])
def autocomplete():
    with driver.session() as session:
        tools_graph = session.run("""
                match (n:InferedTool), (d:Database)
                with collect(n) as cn, collect(d) as cd
                with cn+cd as tools_nodes
                unwind tools_nodes as tools
                return distinct tools.name as name
            """)
            
        tools = [tool["name"] for tool in tools_graph]
    return Response(json.dumps(tools), mimetype='application/json')


class SearchTopic(Form):
    autocomp = TextField('Insert Topic', id='topic_autocomplete2')
 
 
@app.route('/_autocomplete2', methods=['GET'])
def autocomplete2():
    with driver.session() as session:
        topics_graph = session.run("""
            match (k:Keyword)
            where (k)<-[:TOPIC]-() or (k)-[:SUBCLASS{type:"topic"}]-()
            return distinct k.label as label
        """)
        topics = [topic["label"].replace("_", " ") for topic in topics_graph]
    return Response(json.dumps(topics), mimetype='application/json')
 
 
@app.route('/', methods=['GET', 'POST'])
def index():
    tool = SearchTool(request.form)
    topic = SearchTopic(request.form)
    return render_template("algo_100_best.html", tool=tool, topic=topic)
 
if __name__ == '__main__':
    app.run(debug=True)
