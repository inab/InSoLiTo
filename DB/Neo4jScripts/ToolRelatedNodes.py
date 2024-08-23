
def create_tools_nodes(driver, dict_config):
    with driver.session() as session:
        session.run("""MATCH ()-[r:USE_LANGUAGE]->() DELETE r""")
        session.run("""MATCH ()-[r:USE_OS]->() DELETE r""")
        session.run("""MATCH ()-[r:HAS_TYPE]->() DELETE r""")

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
        session.run("""MATCH (r:TypeTool) DELETE r""")
        session.run("""MATCH (r:Language) DELETE r""")
        session.run("""MATCH (r:OS) DELETE r""")

        # Creating keywords nodes
        # name: URL of the EDAM ontology term
        # label: Human readable ID of the keyword
        print("Creating Keyword nodes")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            with csv.edam_id as csvedam, csv.readableID as csvreadableID
            CREATE (p:Keyword {edam: csvedam, label: csvreadableID})
            """ % (dict_config["keyword_nodes"]))
        
        # Creating Tools nodes
        # name: Name of the tool
        # label: Label in bio.tools
        print("Creating Tool nodes")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            CREATE (p:Tool {name: csv.name, label: csv.label})
            """ % (dict_config["tool_nodes"]))
        
        # Creating Type of tool nodes
        # name: Name of the type of tool
        print("Creating Type of tool nodes")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            CREATE (p:TypeTool {name: csv.Type})
            """ % (dict_config["type_nodes"]))
        
        # Creating Tool-TypeTool edges
        print("Creating HAS_TYPE edges")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            MATCH (t:Tool {label:csv.label}),(k:TypeTool {name:csv.Type})
            CREATE (t)-[:HAS_TYPE]->(k)
            """ % (dict_config["tool_type_edges"]))
        
        # Creating Language nodes
        # name: Name of the programming language
        print("Creating Languages nodes")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            CREATE (p:Language {name: csv.Language})
            """ % (dict_config["language_nodes"]))
        
        # Creating Tool-Language edges
        print("Creating USE_LANGUAGE edges")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            MATCH (t:Tool {label:csv.label}),(k:Language {name:csv.Language})
            CREATE (t)-[:USE_LANGUAGE]->(k)
            """ % (dict_config["tool_language_edges"]))

        # Creating Operative system nodes
        # name: Name of the operative system
        print("Creating OS nodes")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            CREATE (p:OS {name: csv.name})
            """ % (dict_config["operative_system_nodes"]))

        # Creating Tool-OS edges
        print("Creating USE_OS edges")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            MATCH (t:Tool {label:csv.label}),(k:OS {name:csv.os})
            CREATE (t)-[:USE_OS]->(k)
            """ % (dict_config["tool_os_edges"]))
        
        # Creating Keyword edges
        list_edam = list(map(str.strip, dict_config["edam_terms_nodes"].strip('][').replace('"', '').split(',')))

        list_edam_relationships = ["INPUTDATA", "INPUTFORMAT", "OUTPUTDATA", "OUTPUTFORMAT", "TOPIC", "OPERATION"]
        
        for i in range(len(list_edam_relationships)):
            print(f"Creating {list_edam_relationships[i]} edges")
            session.run("""
                LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
                MATCH (t:Tool {label:csv.label}),(k:Keyword {edam:csv.keyword})
                CREATE (t)-[:%s]->(k)
                """ % (list_edam[i], list_edam_relationships[i]))
        
        # Creating Subclass edges for keywords
        # :SUBCLASS: Keyword is subclass of the other keyword
        print("Creating SUBCLASS edges")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            MATCH (t:Keyword {edam:csv.edam_id}),(k:Keyword {edam:csv.subclass_edam})
            CREATE (k)-[:SUBCLASS {type:csv.subclass_type}]->(t)
            """ % (dict_config["subclass_edam_nodes"]))

        # Creating Tool-Publications edges
        # :HAS_TOOL: Label of the edges
        print("Creating Tool-Publication edges")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
            MATCH (t:Tool {label:csv.label}),(p:Publication {id:csv.Publication_id})
            CREATE (p)-[:HAS_TOOL]->(t)
            """ % (dict_config["tool_publication_nodes"]))
