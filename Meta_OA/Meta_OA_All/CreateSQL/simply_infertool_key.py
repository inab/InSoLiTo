# Import libraries
import sqlite3
import time

# Start time - Just to count how much the script lasts
start_time = time.time()

# Name of the database
DB_FILE = "database/All_META_OA.db"

# Connect to the SQLite database
# If name not found, it will create a new database
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Create InferedTools table - It will be used to create Tool nodes
# name: Name of the InferedTool
c.execute('''DROP TABLE IF EXISTS InferedTools''')
c.execute('''CREATE TABLE IF NOT EXISTS "InferedTools" (
                "name" TEXT NOT NULL,
                "label" TEXT,
	            PRIMARY KEY("name")
            )''')

c.execute('''DROP TABLE IF EXISTS Languages''')
c.execute('''CREATE TABLE IF NOT EXISTS "Languages" (
                "Language" TEXT NOT NULL,
                PRIMARY KEY("Language")
            )''')

c.execute('''DROP TABLE IF EXISTS InferedTools_to_Languages''')
c.execute('''CREATE TABLE IF NOT EXISTS "InferedTools_to_Languages" (
                "Language" TEXT NOT NULL,
                "name_tool" TEXT NOT NULL,
                UNIQUE(Language, name_tool), 
	            FOREIGN KEY("Language") REFERENCES "Languages"("Language"),
                FOREIGN KEY("name_tool") REFERENCES "InferedTools"("name")
            )''')

c.execute('''DROP TABLE IF EXISTS Operative_systems''')
c.execute('''CREATE TABLE IF NOT EXISTS "Operative_systems" (
                "name" TEXT NOT NULL,
                PRIMARY KEY("name")
            )''')

c.execute('''DROP TABLE IF EXISTS InferedTools_to_OS''')
c.execute('''CREATE TABLE IF NOT EXISTS "InferedTools_to_OS" (
                "os" TEXT NOT NULL,
                "name_tool" TEXT NOT NULL,
                UNIQUE(os, name_tool),
                FOREIGN KEY("name_tool") REFERENCES "InferedTools"("name")
            )''')

# Create InferedTools-Publications table - It will be used to create InferedTools-Publications edges
# name: Name of InferedTool
# Publication_id: Id of a Publication
c.execute('''DROP TABLE IF EXISTS InferedTools_to_Publications''')
c.execute('''CREATE TABLE IF NOT EXISTS "InferedTools_to_Publications" (
                "name" TEXT NOT NULL,
                "Publication_id" TEXT NOT NULL,
                FOREIGN KEY("name") REFERENCES "InferedTools"("name"),
                FOREIGN KEY("Publication_id") REFERENCES "Publications"("id")
            )''')

# Create Keywords table - It will be used to create InferedTools-Publications edges
# edam_id: Identifier of the EDAM
# readableID: Human readable label of the EDAM id
c.execute('''DROP TABLE IF EXISTS Keywords''')
c.execute('''CREATE TABLE IF NOT EXISTS "Keywords" (
                "edam_id" TEXT NOT NULL,
                "readableID" TEXT NOT NULL,
                PRIMARY KEY("edam_id")
            )''')

list_keywords = ["Input_data","Input_format","Output_data",
                    "Output_format","Topics","Operations"]
for keywords in list_keywords:
    c.execute(f'''DROP TABLE IF EXISTS {keywords}''')
    c.execute(f'''CREATE TABLE IF NOT EXISTS "{keywords}" (
                    "name" TEXT NOT NULL,
                    "{keywords.lower()}" TEXT,
                    UNIQUE(name, {keywords.lower()}),                
                    FOREIGN KEY("name") REFERENCES "InferedTools"("name"),
                    FOREIGN KEY("{keywords.lower()}") REFERENCES "Keywords"("edam_id")
                )''')


list_databases = ["MetaGraph","MetaMolecular","MetaProteomics",
                  "OAComparative","OAMolecular","OAProteomics"]

for ind_database in range(len(list_databases)):
    c.execute(f"ATTACH DATABASE 'database/{list_databases[ind_database]}.db' AS {list_databases[ind_database]};")
    c.execute(f"\
        INSERT OR IGNORE INTO InferedTools \
        (name, label) \
        SELECT name, label \
        FROM {list_databases[ind_database]}.InferedTools ;")
    conn.commit()
    c.execute(f"\
        INSERT OR IGNORE INTO Languages \
        (Language) \
        SELECT Language \
        FROM {list_databases[ind_database]}.Languages ;")
    conn.commit()
    c.execute(f"\
        INSERT OR IGNORE INTO InferedTools_to_Languages \
        (Language, name_tool) \
        SELECT Language, name_tool \
        FROM {list_databases[ind_database]}.InferedTools_to_Languages ;")
    conn.commit()
    c.execute(f"\
        INSERT OR IGNORE INTO Operative_systems \
        (name) \
        SELECT name \
        FROM {list_databases[ind_database]}.Operative_systems ;")
    conn.commit()

    c.execute(f"\
        INSERT OR IGNORE INTO InferedTools_to_OS \
        (os, name_tool) \
        SELECT os, name_tool \
        FROM {list_databases[ind_database]}.InferedTools_to_OS ;")
    conn.commit()
    c.execute(f"\
        INSERT OR IGNORE INTO InferedTools_to_Publications \
        (name, Publication_id) \
        SELECT name, Publication_id \
        FROM {list_databases[ind_database]}.InferedTools_to_Publications ;")
    conn.commit()
    c.execute(f"\
        INSERT OR IGNORE INTO Keywords \
        (edam_id, readableID) \
        SELECT edam_id, readableID \
        FROM {list_databases[ind_database]}.Keywords ;")
    conn.commit()
    c.execute(f"\
        INSERT OR IGNORE INTO Operative_systems \
        (name) \
        SELECT name \
        FROM {list_databases[ind_database]}.Operative_systems ;")
    conn.commit()
    
    for keywords in list_keywords:
        c.execute(f"\
            INSERT OR IGNORE INTO {keywords} \
            (name, {keywords.lower()}) \
            SELECT name, {keywords.lower()} \
            FROM {list_databases[ind_database]}.{keywords} ;")
        conn.commit()

c.close()
print("--- %s seconds ---" % (time.time() - start_time))

