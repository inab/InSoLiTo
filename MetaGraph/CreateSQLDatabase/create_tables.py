# Import libraries
import sqlite3
import time


# Start time - Just to count how much the script lasts
start_time = time.time()

# Name of the database
DB_FILE = "database/Namedatabase.db"

# Connect to the SQLite database
# If name not found, it will create a new database
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Create Publications table - It will be used to create Publication nodes
# id: Primary key of the publication
# title: Title of the publication
# year: Year of the publication
# pmcid: PMCID of the publication
# pmid: PMID of the publication
# doi: DOI of the publication
c.execute('''DROP TABLE IF EXISTS Publications''')
c.execute('''CREATE TABLE IF NOT EXISTS "Publications" (
	            "id"	TEXT NOT NULL,
	            "title"	TEXT NOT NULL,
	            "year" INTEGER,
	            "pmcid" TEXT,
	            "pmid" TEXT,
	            "doi" TEXT,
	            PRIMARY KEY("id")
            )''')


# Create Citations table - It will be used to create Publication-Publication edges
# id1: Foreign key of publication
# id2: Foreign key of the second publication
# n_citations: Number of co-occurences between publications
# year: Year when the co-occurence happenend.
c.execute('''DROP TABLE IF EXISTS Citations''')
c.execute('''CREATE TABLE "Citations" (
                "id1"	TEXT NOT NULL,
                "id2"	TEXT NOT NULL,
                "n_citations" INTEGER,
                "year" INTEGER,
                FOREIGN KEY("id1") REFERENCES "Publications"("id"),
                FOREIGN KEY("id2") REFERENCES "Publications"("id")
            );''')

c.execute('''DROP TABLE IF EXISTS Citations_backup''')

# Create InferedTools table - It will be used to create Tool nodes
# name: Name of the InferedTool
c.execute('''DROP TABLE IF EXISTS InferedTools''')
c.execute('''CREATE TABLE IF NOT EXISTS "InferedTools" (
                "name" TEXT NOT NULL,
                "label" TEXT,
	            PRIMARY KEY("name")
            )''')

# Create Languages table - Table storing all the programming languages of the tools
# Language: Name of the programming language
c.execute('''DROP TABLE IF EXISTS Languages''')
c.execute('''CREATE TABLE IF NOT EXISTS "Languages" (
                "Language" TEXT NOT NULL,
                PRIMARY KEY("Language")
            )''')

# Table for the relationships between the tools and its programming languages
# Language: Name of the programming language
# name_tool: Name of the tool
c.execute('''DROP TABLE IF EXISTS InferedTools_to_Languages''')
c.execute('''CREATE TABLE IF NOT EXISTS "InferedTools_to_Languages" (
                "Language" TEXT NOT NULL,
                "name_tool" TEXT NOT NULL,
                UNIQUE(Language, name_tool), 
	            FOREIGN KEY("Language") REFERENCES "Languages"("Language"),
                FOREIGN KEY("name_tool") REFERENCES "InferedTools"("name")
            )''')

# Create Operative systems table - Table storing all the operative systems of the tools
# name: Name of the operative system
c.execute('''DROP TABLE IF EXISTS Operative_systems''')
c.execute('''CREATE TABLE IF NOT EXISTS "Operative_systems" (
                "name" TEXT NOT NULL,
                PRIMARY KEY("name")
            )''')

# Table for the relationships between the tools and its operative systems
# os: Name of the operative system
# name_tool: Name of the tool
c.execute('''DROP TABLE IF EXISTS InferedTools_to_OS''')
c.execute('''CREATE TABLE IF NOT EXISTS "InferedTools_to_OS" (
                "os" TEXT NOT NULL,
                "name_tool" TEXT NOT NULL,
                UNIQUE(os, name_tool),
                FOREIGN KEY("name_tool") REFERENCES "InferedTools"("name")
            )''')

# Create InferedTools-Publications table - It will be used to connect the tools and the publications that describe the tool
# name: Name of InferedTool node.
# Publication_id: Id of a Publication.
c.execute('''DROP TABLE IF EXISTS InferedTools_to_Publications''')
c.execute('''CREATE TABLE IF NOT EXISTS "InferedTools_to_Publications" (
                "name" TEXT NOT NULL,
                "Publication_id" TEXT NOT NULL,
                FOREIGN KEY("name") REFERENCES "InferedTools"("name"),
                FOREIGN KEY("Publication_id") REFERENCES "Publications"("id")
            )''')

# Create Keywords table - It is used to store all the EDAM ontology terms of the database
# edam_id: Identifier of the EDAM
# readableID: Human readable label of the EDAM id
c.execute('''DROP TABLE IF EXISTS Keywords''')
c.execute('''CREATE TABLE IF NOT EXISTS "Keywords" (
                "edam_id" TEXT NOT NULL,
                "readableID" TEXT NOT NULL,
                PRIMARY KEY("edam_id")
            )''')

list_edam_relationships = ["Input_data", "Input_format",
                           "Output_data", "Output_format",
                           "Topics", "Operations"]
for edam_term in list_edam_relationships:
    
    # Create InferedTools-keywords table - It will be used to relate the EDAM terms and the tools
    # name: Name of the InferedTool
    # Keyword: Name of the EDAM keyword
    c.execute(f'''DROP TABLE IF EXISTS {edam_term}''')
    c.execute(f'''CREATE TABLE IF NOT EXISTS "{edam_term}" (
                    "name" TEXT NOT NULL,
                    "keyword" TEXT,
                    UNIQUE(name, input_data), 
                    FOREIGN KEY("name") REFERENCES "InferedTools"("name"),
                    FOREIGN KEY("keyword") REFERENCES "Keywords"("edam_id")
                )''')
    
c.execute('''DROP TABLE IF EXISTS SubclassEDAM''')
c.execute('''CREATE TABLE IF NOT EXISTS "SubclassEDAM" (
                "edam_id" TEXT,
                "subclass_edam" ,
                UNIQUE(edam_id, subclass_edam)                
            )''')

conn.commit()

c.close()




