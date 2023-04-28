# Import libraries
import json
from owlready2 import *
from urllib.request import urlopen

def checkExist(type, id):
    if type=="pmid":
        # TO DO: Create a table where the Publications in the Citations table are stored
        # So, we will do queries to a 10th times smaller table (35M vs. 3.6M)
        c.execute(f"""
            SELECT pmid FROM PublicationsInCitations WHERE pmid={id}
            limit 1
            """)
    else:
        c.execute(f"""
            SELECT pmid FROM PublicationsInCitations WHERE doi='{id}'
            limit 1
            """)
    pmids=c.fetchall()
    for pmid in pmids:
        return pmid[0]

# Function to store the different types of EDAM in the Keywords table
# It also stores the EDAM terms in their Human Readable format
def retrieve_in_out_operations(set_keywords):
    for keywords in set_keywords:
        # Take the id of the edam
        name=keywords.split("/")[3]
        # Function to know the full name of the ID in owlready2
        label = f"onto.{name}.label"
        labels = eval(label)
        # Insert the Id and name into the database
        for label in labels:
            c.execute(f"""INSERT OR IGNORE INTO Keywords
                            values ('{keywords}', '{label}')""")
    
# Function to store the Topics in the Keywords table
# It also stores the EDAM terms in their Human Readable format
def retrieve_topic(topics):
    for topic in topics:
        # Take the ID of the edam
        name=topic.split("/")[3]
        # Function to know the full name of the ID in owlready2
        Ids = f"onto.{name}.hasHumanReadableId"
        try:
            # Run the function
            Ids=eval(Ids)
            # Insert the Id and name into the database
            for Id in Ids:
                Id = Id.replace("_"," ")
                c.execute(f"""INSERT OR IGNORE INTO Keywords
                            values ('{topic}', '{Id}')""")
        except:
            continue
    
# Function to search the different types of EDAM terms for each tool of OpenEBench
# The types are the following: Input data, Input format, Output data, Output format, Operations and Topics 
def retrieve_keywords(i):
    # Initialize EDAM types sets
    dict_keywords = {"InputData":set(),"InputFormat":set(),"OutputData":set(),"OutputFormat":set(),"Topics":set(),"Operations":set()}
     
    # If there are no EDAM terms, exit the function
    if "semantics" not in i:
        return dict_keywords
    # Search all the types of EDAM in the tool
    # Search the Input terms
    for inputs in i["semantics"]["inputs"]:
        #Check if the is Input data
        if "datatype" in inputs:
            #Store all the Input data EDAM terms
            dict_keywords["InputData"].add(inputs["datatype"])
        #Store all the Input format EDAM terms
        for formats in inputs["formats"]:
            dict_keywords["InputFormat"].add(formats)
    # Same as input
    for outputs in i["semantics"]["outputs"]:
        if "datatype" in outputs:
            dict_keywords["OutputData"].add(outputs["datatype"])
        for formats in outputs["formats"]:
            dict_keywords["OutputFormat"].add(formats)
    # Store the Operation EDAM terms
    for operations in i["semantics"]["operations"]:
        dict_keywords["Operations"].add(operations)
    # Store the Topics EDAM terms
    for topics in i["semantics"]["topics"]:
        dict_keywords["Topics"].add(topics)
    # Store the Topic in the database
    retrieve_topic(dict_keywords["Topics"])
    # Store all the different EDAM types in the database
    retrieve_in_out_operations(dict_keywords["InputData"])
    retrieve_in_out_operations(dict_keywords["InputFormat"])
    retrieve_in_out_operations(dict_keywords["OutputData"])
    retrieve_in_out_operations(dict_keywords["OutputFormat"])
    retrieve_in_out_operations(dict_keywords["Operations"])

    return dict_keywords

def retrieveOEBInformation(publication):

    listKeywords = {"InputData":set(),"InputFormat":set(),"OutputData":set(),"OutputFormat":set(),"Topics":set(),"Operations":set()}
    # Function to retrieve all its EDAM terms
    dict_keywords=retrieve_keywords(publication)
    for keys, values in dict_keywords.items():
        listKeywords[keys] = listKeywords[keys].union(values)

    typeTool = publication["@type"]

    setLanguages = set()
    setOs = set()
        # Retrieve its Name, label Languages and OS
    if "languages" in publication:
        for lang in publication["languages"]:
            setLanguages.add(lang)
    if "os" in publication:
        for os in publication["os"]:
            setOs.add(os)
    name= publication["name"]
    label=publication["@label"]

    return listKeywords, typeTool, setLanguages, setOs, name, label
    
# Function for inserting the EDAM terms into the database`
def insert_keywords(name, keywords, name_table):
    for keyword in keywords:
        c.execute(f""" INSERT OR IGNORE INTO {name_table}
                            values ('{name}', '{keyword}')""")

def create_Tools(c_para, conn_para):
    # Put the database variables as global variables. So they can work with all the functions
    global c
    c = c_para
    global conn
    conn = conn_para
    # Load all the EDAM Ontology
    global onto
    onto = get_ontology("http://edamontology.org/EDAM.owl").load()
    
    
    #Put the reduction of table Publications to table "PublicationsInCitations"
    # It would reduce the query time response
    
    c.execute('''DROP TABLE IF EXISTS PublicationsInCitations''')
    c.execute('''CREATE TABLE PublicationsInCitations AS
        SELECT  p.title,p.year,p.doi, p.pmid
                from Publications as p
                INNER JOIN Citations as c ON
                p.pmid == c.id1
                union
                SELECT p.title,p.year,p.doi, p.pmid
                from Publications as p
                INNER JOIN Citations as c ON
                p.pmid == c.id2
            ''')
    conn.commit()
    
    # Open the file with the information of all tools from OpenEBench
    # File is following API search: "https://openebench.bsc.es/monitor/rest/search?=publications"
    url_OEB="https://openebench.bsc.es/monitor/rest/search?=publications"
    response = urlopen(url_OEB)
    # Store the tool information in this variable
    data_json = json.loads(response.read())

    print("enter parsing")
    for obj in data_json:
        isTool=False
        listId = set()
        # if len(obj["publications"]):
        if "publications" not in obj:
            continue
        if len(obj["publications"]):
            
            for publication in obj["publications"]:
                if "pmid" in publication:
                    # print(publication["pmid"])
                    pmidid = int(publication["pmid"])
                    pmidId = checkExist("pmid",pmidid)
                elif "doi" in publication:
                    pmidId = checkExist("doi", publication["doi"])
                if not pmidId:
                    continue
                isTool = True
                listId.add(pmidId)
        if not isTool:
            continue
        listKeywords, typeTool, setLanguages, setOs, name, label = retrieveOEBInformation(obj)
        print(listId, listKeywords, typeTool, setLanguages, setOs, name, label)
        # If the tool is found, we can store it in the database
        c.execute(f"""INSERT OR IGNORE INTO Tools
                        values ('{name}', '{label}')""")
        
        # If the tool has Type of software information
        if typeTool:
            # Insert to the table with all the Programming languages
            c.execute(f"""INSERT  OR IGNORE INTO TypeTool
                        VALUES ('{typeTool}')""")
            # Insert the relationships between Tools and Languages
            c.execute(f"""INSERT OR IGNORE INTO ToolsToTypeTool
                        VALUES ('{typeTool}', '{label}')""")
        # If the tool has Programming Language information
        if setLanguages:
            # Store the languages in the database
            for language in setLanguages:
                # Insert to the table with all the Programming languages
                c.execute(f"""INSERT OR IGNORE INTO Languages
                            VALUES ('{language}')""")
                # Insert the relationships between Tools and Languages
                c.execute(f"""INSERT OR IGNORE INTO ToolsToLanguages
                            VALUES ('{language}', '{label}')""")
        # If the tool has Operative System information
        if setOs:
            # Store the OS in the database
            for op_sys in setOs:
                # Insert to the table with all the OS
                c.execute(f"""INSERT OR IGNORE INTO OperativeSystems
                            VALUES ('{op_sys}')""")
                # Insert the relationships between Tools and OS
                c.execute(f"""INSERT OR IGNORE INTO ToolsToOS
                            VALUES ('{op_sys}', '{label}')""")
        # If the tool has EDAM keywords, store them by type of keyword            
        if listKeywords:
            for typeKeyword, keywords in listKeywords.items():
                insert_keywords(label, keywords, typeKeyword)

        for pmid in listId:
            # Store the relationship between article and the tool that it describes with the information from OpenEBench
            c.execute(f'''INSERT OR IGNORE INTO ToolsToPublications
                    values ("{label}","{pmid}")''')
            
            # Udate MetaCitation with the name of the tools
            c.execute(f'''UPDATE MetaCitations
                            SET id1 = "{label}"
                            WHERE id1 = "{pmid}" ''')
            c.execute(f'''UPDATE MetaCitations
                            SET id2 = "{label}"
                            WHERE id2 = "{pmid}" ''')
            conn.commit()

    # Sort the values in columns to sum well all the citations
    c.execute("""
        UPDATE MetaCitations
            SET id1 = id2, 
            id2 = id1
            WHERE id1 > id2
        """)

    #Sum all the n_citations from all the tools with the same values (in case we have the same co-occurence in the same year for more than one publication from a tool)
    c.execute("""
        CREATE TABLE MetaCitations_backup AS
        Select id1,id2, sum(n_citations) as n_citations, year
        from MetaCitations
        group by id1,id2, year
        """)
    #We drop the table and then change the name to update the table
    c.execute("""DROP TABLE MetaCitations""")
    c.execute("""
        ALTER TABLE MetaCitations_backup
        RENAME TO MetaCitations;
        """)
    
    # Create MetaCitationsReduction table - Same as MetaCitations without Article-Article relationships
    c.execute('''DROP TABLE IF EXISTS MetaCitationsReduction''')
    c.execute('''CREATE TABLE MetaCitationsReduction AS
                select *
            from MetaCitations
            WHERE CAST(id1 AS INTEGER) IS NOT id1 or CAST(id2 AS INTEGER) IS NOT id2;
            ''')
    
    #Put the reduction of table Publications to table "PublicationsInMetaCitations"
    # It would give less non-used information to the graph
    
    c.execute('''DROP TABLE IF EXISTS PublicationsInMetaCitations''')
    c.execute('''CREATE TABLE PublicationsInMetaCitations AS
        SELECT  p.title,p.year,p.doi, p.pmid
                from Publications as p
                INNER JOIN MetaCitationsReduction as c ON
                p.pmid == c.id1
                union
                SELECT p.title,p.year,p.doi, p.pmid
                from Publications as p
                INNER JOIN MetaCitationsReduction as c ON
                p.pmid == c.id2
            ''')

