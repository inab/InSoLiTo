

def create_SQL_tables(c):
        
    # Create Publications table - It will be used to create Publication nodes
    # id: Primary key of the publication
    # title: Title of the publication
    # year: Year of the publication
    # pmcid: PMCID of the publication
    # pmid: PMID of the publication
    # doi: DOI of the publication
    #c.execute('''DROP TABLE IF EXISTS Publications''')
    #c.execute('''CREATE TABLE IF NOT EXISTS "Publications" (
                    #"title"	TEXT NOT NULL,
                    #"year" INTEGER,
                    #"pmcid" TEXT,
                    #"pmid" TEXT,
                    #"doi" TEXT
                #);''')
    #c.execute('''
        #CREATE UNIQUE INDEX idx_Publications
        #ON Publications (doi);
    #''')


    # Create Citations table - It will be used to create Publication-Publication edges
    # id1: Foreign key of publication
    # id2: Foreign key of the second publication
    # n_citations: Number of co-occurences between publications
    # year: Year when the co-occurence happenend.
    #c.execute('''DROP TABLE IF EXISTS Citations''')
    #c.execute('''CREATE TABLE "Citations" (
                    #"id1"	TEXT NOT NULL,
                    #"id2"	TEXT NOT NULL,
                    #"n_citations" INTEGER,
                    #"year" INTEGER
                #);''')

    #c.execute('''DROP TABLE IF EXISTS Citations_backup''')

    #Create Tools table - It will be used to create Tool nodes
    #name: Name of the InferedTool
    c.execute('''DROP TABLE IF EXISTS Tools''')
    c.execute('''CREATE TABLE IF NOT EXISTS "Tools" (
                    "name" TEXT NOT NULL,
                    "label" TEXT,
                    PRIMARY KEY("label")
                )''')
    
    #Create Languages table - Table storing all the programming languages of the tools
    #Language: Name of the programming language
    c.execute('''DROP TABLE IF EXISTS TypeTool''')
    c.execute('''CREATE TABLE IF NOT EXISTS "TypeTool" (
                    "Type" TEXT NOT NULL,
                    PRIMARY KEY("Type")
                )''')

    #Table for the relationships between the tools and its programming languages
    #Language: Name of the programming language
    #label: Name of the tool
    c.execute('''DROP TABLE IF EXISTS ToolsToTypeTool''')
    c.execute('''CREATE TABLE IF NOT EXISTS "ToolsToTypeTool" (
                    "Type" TEXT NOT NULL,
                    "label" TEXT NOT NULL,
                    UNIQUE(Type, label), 
                    FOREIGN KEY("Type") REFERENCES "TypeTool"("Type"),
                    FOREIGN KEY("label") REFERENCES "Tools"("label")
                )''')

    #Create Languages table - Table storing all the programming languages of the tools
    #Language: Name of the programming language
    c.execute('''DROP TABLE IF EXISTS Languages''')
    c.execute('''CREATE TABLE IF NOT EXISTS "Languages" (
                    "Language" TEXT NOT NULL,
                    PRIMARY KEY("Language")
                )''')

    #Table for the relationships between the tools and its programming languages
    #Language: Name of the programming language
    #label: Name of the tool
    c.execute('''DROP TABLE IF EXISTS ToolsToLanguages''')
    c.execute('''CREATE TABLE IF NOT EXISTS "ToolsToLanguages" (
                    "Language" TEXT NOT NULL,
                    "label" TEXT NOT NULL,
                    UNIQUE(Language, label), 
                    FOREIGN KEY("Language") REFERENCES "Languages"("Language"),
                    FOREIGN KEY("label") REFERENCES "Tools"("label")
                )''')

    #Create Operative systems table - Table storing all the operative systems of the tools
    #name: Name of the operative system
    c.execute('''DROP TABLE IF EXISTS OperativeSystems''')
    c.execute('''CREATE TABLE IF NOT EXISTS "OperativeSystems" (
                    "name" TEXT NOT NULL,
                    PRIMARY KEY("name")
                )''')

    #Table for the relationships between the tools and its operative systems
    #os: Name of the operative system
    #label: Name of the tool
    c.execute('''DROP TABLE IF EXISTS ToolsToOS''')
    c.execute('''CREATE TABLE IF NOT EXISTS "ToolsToOS" (
                    "os" TEXT NOT NULL,
                    "label" TEXT NOT NULL,
                    UNIQUE(os, label),
                    FOREIGN KEY("label") REFERENCES "Tools"("label")
                )''')

    #Create InferedTools-Publications table - It will be used to connect the tools and the publications that describe the tool
    #label: Name of InferedTool node.
    #Publication_id: Id of a Publication.
    c.execute('''DROP TABLE IF EXISTS ToolsToPublications''')
    c.execute('''CREATE TABLE IF NOT EXISTS "ToolsToPublications" (
                    "label" TEXT NOT NULL,
                    "Publication_id" TEXT NOT NULL,
                    FOREIGN KEY("label") REFERENCES "Tools"("label"),
                    FOREIGN KEY("Publication_id") REFERENCES "Publications"("id")
                )''')

    #Create Keywords table - It is used to store all the EDAM ontology terms of the database
    #edam_id: Identifier of the EDAM
    #readableID: Human readable label of the EDAM id
    c.execute('''DROP TABLE IF EXISTS Keywords''')
    c.execute('''CREATE TABLE IF NOT EXISTS "Keywords" (
                    "edam_id" TEXT NOT NULL,
                    "readableID" TEXT NOT NULL,
                    PRIMARY KEY("edam_id")
                )''')

    list_edam_relationships = ["InputData", "InputFormat",
                            "OutputData", "OutputFormat",
                            "Topics", "Operations"]
    for edam_term in list_edam_relationships:
        
        #Create InferedTools-keywords table - It will be used to relate the EDAM terms and the tools
        #label: Name of the InferedTool
        #Keyword: Name of the EDAM keyword
        c.execute(f'''DROP TABLE IF EXISTS {edam_term}''')
        c.execute(f'''CREATE TABLE IF NOT EXISTS "{edam_term}" (
                        "label" TEXT NOT NULL,
                        "keyword" TEXT,
                        UNIQUE(label, keyword), 
                        FOREIGN KEY("label") REFERENCES "InferedTools"("label"),
                        FOREIGN KEY("keyword") REFERENCES "Keywords"("edam_id")
                    )''')
        
    c.execute('''DROP TABLE IF EXISTS SubclassEDAM''')
    c.execute('''CREATE TABLE IF NOT EXISTS "SubclassEDAM" (
                    "edam_id" TEXT,
                    "subclass_edam" TEXT,
                    "subclass_type" TEXT,
                    UNIQUE(edam_id, subclass_edam)                
                )''')




