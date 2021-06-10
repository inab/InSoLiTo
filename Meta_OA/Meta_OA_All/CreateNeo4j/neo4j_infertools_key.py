# Import libraries
from neo4j import GraphDatabase
import time

# Start time - Just to count how much the script lasts
start_time = time.time()

# URL of the Neo4j Server
uri = "bolt://localhost:7687"
# Driver to connect to the Server with the author and the password
# To be able to use it, you need to open your neo4j server before
driver = GraphDatabase.driver(uri, auth=("neo4j", "1234"))

def graph():
    with driver.session() as session:
        session.run("""MATCH ()-[r:USE_LANGUAGE]->() DELETE r""")
        session.run("""MATCH ()-[r:USE_OS]->() DELETE r""")
        
        session.run("""MATCH ()-[r:HAS_TOOL]->() DELETE r""")
        session.run("""MATCH ()-[r:METAOCCUR]->() DELETE r""")
        
        session.run("""MATCH ()-[r:INPUTDATA]->() DELETE r""")
        session.run("""MATCH ()-[r:INPUTFORMAT]->() DELETE r""")
        session.run("""MATCH ()-[r:OUTPUTDATA]->() DELETE r""")
        session.run("""MATCH ()-[r:OUTPUTFORMAT]->() DELETE r""")
        session.run("""MATCH ()-[r:TOPIC]->() DELETE r""")
        session.run("""MATCH ()-[r:OPERATION]->() DELETE r""")
        
        session.run("""MATCH ()-[r:SUBCLASS]->() DELETE r""")

        
        session.run("""MATCH (r:Keyword) DELETE r""")
        session.run("""MATCH (r:Language) DELETE r""")
        session.run("""MATCH (r:OS) DELETE r""")
        
        #Creating keywords nodes
        # edam: Identifier of the edam ontology
        # label: Human Readable Edam id
        print("Creating Keyword nodes")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Keywords.csv" AS csv
            with csv.edam_id as csvedam, csv.readableID as csvreadableID
            CREATE (p:Keyword {edam: csvedam, label: csvreadableID})
            """)
        #Creating InferedTools nodes
        # Label of the edges
        print("Creating InferedTool nodes")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///InferedTools.csv" AS csv
            MERGE (p:InferedTool {name: csv.name, label: csv.label})
            """)
        
        print("Creating Languages nodes")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Languages.csv" AS csv
            CREATE (p:Language {name: csv.Language})
            """)
        
        print("Creating USE_LANGUAGE edges")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///InferedTools_to_Languages.csv" AS csv
            MATCH (t:InferedTool {name:csv.name_tool}),(k:Language {name:csv.Language})
            CREATE (t)-[:USE_LANGUAGE]->(k)
            """)
        
        print("Creating OS nodes")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Operative_systems.csv" AS csv
            CREATE (p:OS {name: csv.name})
            """)
        
        print("Creating USE_OS edges")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///InferedTools_to_OS.csv" AS csv
            MATCH (t:InferedTool {name:csv.name_tool}),(k:OS {name:csv.os})
            CREATE (t)-[:USE_OS]->(k)
            """)
        
        #Creating Tool-Publications edges
        # :HAS_TOOL: Label of the edges
        print("Creating INPUTDATA edges")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Input_data.csv" AS csv
            MATCH (t:InferedTool {name:csv.name}),(k:Keyword {edam:csv.input_data})
            CREATE (t)-[:INPUTDATA]->(k)
            """)
        #Creating Tool-Publications edges
        # :HAS_TOOL: Label of the edges
        print("Creating INPUTFORMAT edges")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Input_format.csv" AS csv
            MATCH (t:InferedTool {name:csv.name}),(k:Keyword {edam:csv.input_format})
            CREATE (t)-[:INPUTFORMAT]->(k)
            """)
                
        #Creating Tool-Publications edges
        # :HAS_TOOL: Label of the edges
        print("Creating OUTPUTDATA edges")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Output_data.csv" AS csv
            MATCH (t:InferedTool {name:csv.name}),(k:Keyword {edam:csv.output_data})
            CREATE (t)-[:OUTPUTDATA]->(k)
            """)        
        #Creating Tool-Publications edges
        # :HAS_TOOL: Label of the edges
        print("Creating OUTPUTFORMAT edges")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Output_format.csv" AS csv
            MATCH (t:InferedTool {name:csv.name}),(k:Keyword {edam:csv.output_format})
            CREATE (t)-[:OUTPUTFORMAT]->(k)
            """)        
        #Creating Tool-Publications edges
        # :HAS_TOOL: Label of the edges
        print("Creating TOPIC edges")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Topics.csv" AS csv
            MATCH (t:InferedTool {name:csv.name}),(k:Keyword {edam:csv.topics})
            CREATE (t)-[:TOPIC]->(k)
            """)        
        #Creating Tool-Publications edges
        # :HAS_TOOL: Label of the edges
        print("Creating OPERATION edges")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Operations.csv" AS csv
            MATCH (t:InferedTool {name:csv.name}),(k:Keyword {edam:csv.operations})
            CREATE (t)-[:OPERATION]->(k)
            """)
        
        # Creating Subclass edges for keywords
        # :SUBCLASS: Keyword is subclass of the other keyword
        print("Creating SUBCLASS edges")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///SubclassEDAM.csv" AS csv
            MATCH (t:Keyword {edam:csv.edam_id}),(k:Keyword {edam:csv.subclass_edam})
            CREATE (k)-[:SUBCLASS]->(t)
            """)

        #Creating Tool-Publications edges
        # :HAS_TOOL: Label of the edges
        print("Creating Tool-Publication edges")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///InferedTools_to_Publications.csv" AS csv
            MATCH (t:InferedTool {name:csv.name}),(p:Publication {id:csv.Publication_id})
            MERGE (p)-[:HAS_TOOL]->(t)
            """)


if __name__ == '__main__':
    graph()
    print("--- %s seconds ---" % (time.time() - start_time))
