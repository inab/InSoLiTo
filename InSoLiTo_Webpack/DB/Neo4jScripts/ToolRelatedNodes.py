
def create_tools_nodes(driver):
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
        #name: URL of the EDAM ontology term
        #label: Human readable ID of the keyword
        print("Creating Keyword nodes")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Keywords.csv" AS csv
            with csv.edam_id as csvedam, csv.readableID as csvreadableID
            CREATE (p:Keyword {edam: csvedam, label: csvreadableID})
            """)
        
        #Creating Tools nodes
        #name: Name of the tool
        #label: Label in bio.tools
        print("Creating Tool nodes")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Tools.csv" AS csv
            CREATE (p:Tool {name: csv.name, label: csv.label})
            """)
        
        #Creating Language nodes
        #name: Name of the programming language
        print("Creating Languages nodes")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Languages.csv" AS csv
            CREATE (p:Language {name: csv.Language})
            """)
        
        #Creating Tool-Language edges        
        print("Creating USE_LANGUAGE edges")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///ToolsToLanguages.csv" AS csv
            MATCH (t:Tool {name:csv.name_tool}),(k:Language {name:csv.Language})
            CREATE (t)-[:USE_LANGUAGE]->(k)
            """)

        #Creating Operative system nodes 
        #name: Name of the operative system
        print("Creating OS nodes")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///OperativeSystems.csv" AS csv
            CREATE (p:OS {name: csv.name})
            """)

        #Creating Tool-OS edges
        print("Creating USE_OS edges")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///ToolsToOS.csv" AS csv
            MATCH (t:Tool {name:csv.name_tool}),(k:OS {name:csv.os})
            CREATE (t)-[:USE_OS]->(k)
            """)
        
        # Creating Keyword edges
        list_edam = ["InputData", "InputFormat",
                           "OutputData", "OutputFormat",
                           "Topics", "Operations"]
        list_edam_relationships = ["INPUTDATA", "INPUTFORMAT",
                           "OUTPUTDATA", "OUTPUTFORMAT",
                           "TOPIC", "OPERATION"]
        
        for i in range(len(list_edam_relationships)):
            print(f"Creating {list_edam_relationships[i]} edges")
            session.run("""
                LOAD CSV WITH HEADERS FROM "file:///%s.csv" AS csv
                MATCH (t:Tool {name:csv.name}),(k:Keyword {edam:csv.keyword})
                CREATE (t)-[:%s]->(k)
                """%(list_edam[i], list_edam_relationships[i]))
        
        # Creating Subclass edges for keywords
        # :SUBCLASS: Keyword is subclass of the other keyword
        print("Creating SUBCLASS edges")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///SubclassEDAM.csv" AS csv
            MATCH (t:Keyword {edam:csv.edam_id}),(k:Keyword {edam:csv.subclass_edam})
            CREATE (k)-[:SUBCLASS {type:csv.subclass_type}]->(t)
            """)

        #Creating Tool-Publications edges
        # :HAS_TOOL: Label of the edges
        print("Creating Tool-Publication edges")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///ToolsToPublications.csv" AS csv
            MATCH (t:Tool {name:csv.name}),(p:Publication {id:csv.Publication_id})
            CREATE (p)-[:HAS_TOOL]->(t)
            """)
