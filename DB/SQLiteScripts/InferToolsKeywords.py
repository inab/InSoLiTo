# Import libraries
import json
from owlready2 import *
from urllib.request import urlopen

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

def retrieveTypeNode(publication):
    return publication["@type"]


def retrieveOEBInformation(publication, is_tool, setDataSource, setListKeywords, setTypeTool, setLanguages, setOs, name, label):
    if "deprecated" in publication:
        return is_tool, setDataSource, setListKeywords, setTypeTool, setLanguages, setOs, name, label
    is_tool=True
    # Look where information comes from (Usually is bio.tools, Bioconda or openEBench)
    setDataSource.add(publication["@nmsp"])
    # Function to retrieve all its EDAM terms
    dict_keywords=retrieve_keywords(publication)
    for keys, values in dict_keywords.items():
        setListKeywords[keys] = setListKeywords[keys].union(values)
    
    setTypeTool.add(retrieveTypeNode(publication))
    # Retrieve its Name, label Languages and OS
    for lang in publication["languages"]:
        setLanguages.add(lang)
    for os in publication["os"]:
        setOs.add(os)
    name.append(publication["name"])
    label.append(publication["@label"])
    return is_tool, setDataSource, setListKeywords, setTypeTool, setLanguages, setOs, name, label
    
# This function search in the JSON file if one of the IDs matches an article from a tool.
# We prioritize the results from the biotools option of @nmsp. If a bioconda or openebench source is found before,
# we must look to all the publications file to see if we find the biotools option. If not, we retrieve the results
# from bioconda or openebench
def search_json(data,doi,pmid):
    # Variable to check if we have found a tool
    is_tool = False
    #Initialize variables
    setDataSource = set()
    setListKeywords = {"InputData":set(),"InputFormat":set(),"OutputData":set(),"OutputFormat":set(),"Topics":set(),"Operations":set()}
    setTypeTool = set()
    setLanguages = set()
    setOs = set()
    name=[]
    label=[]

    # For every article in the Publication table (that is also found in the Citations table)
    for publication in data:
        # If in the article there is no "publications" section, try the next article
        if "publications" not in publication:
            continue   
        # for all the tools that have publications section
        for ids in publication["publications"]:
            # Check if there are Programming Language and Operative System information
            # If not, put an empty list
            if "languages" not in publication:
                publication["languages"] = []
            if "os" not in publication:
                publication["os"] = []
                
            # Check if the DOI from the Publication database and OpenEBench are the same
            # If they match, do the following
            if doi != "None" and "doi" in ids:
                if doi in ids["doi"]:
                    is_tool, setDataSource, setListKeywords, setTypeTool, setLanguages, setOs, name, label = retrieveOEBInformation(publication, is_tool, setDataSource, setListKeywords, setTypeTool, setLanguages, setOs, name, label)
            # Same is DOI but with PMID
            if pmid != "None" and "pmid" in ids:
                if pmid == ids["pmid"]:
                    is_tool, setDataSource, setListKeywords, setTypeTool, setLanguages, setOs, name, label = retrieveOEBInformation(publication, is_tool, setDataSource, setListKeywords, setTypeTool, setLanguages, setOs, name, label)
                    
    if is_tool:
        #Give shortest label (So we get rid of the tools with multiple sufix such as EBI or API)
        minLen=1000
        minLabel=""
        minName=""
        for l in range(len(label)):
            if len(label[l])<minLen:
                minLen=len(label[l])
                minLabel=label[l]
                minName=name[l]
        print(setDataSource,setListKeywords,setTypeTool, setLanguages, setOs, minName, minLabel)

        return minName, minLabel, setTypeTool, setLanguages, setOs, setListKeywords
    # If no information found, return False
    return False, False, False, False, False, False

# Function for inserting the EDAM terms into the database`
def insert_keywords(name, keywords, name_table):
    for keyword in keywords:
        c.execute(f""" INSERT OR IGNORE INTO {name_table}
                            values ('{name}', '{keyword}')""")

# Main function
# Convert Articles into Tools with the information from OpenEBench
# Gather another useful information from the tool: Operative Systems, Languages and EDAM Keywords
def create_Tools( c_para, conn_para):
    # Put the database variables as global variables. So they can work with all the functions
    global c
    c = c_para
    global conn
    conn = conn_para
    # Load all the EDAM Ontology
    global onto
    onto = get_ontology("http://edamontology.org/EDAM.owl").load()
    
    
    # Open the file with the information of all tools from OpenEBench
    # File is following API search: "https://openebench.bsc.es/monitor/rest/search?=publications"
    url_OEB="https://openebench.bsc.es/monitor/rest/search?=publications"
    response = urlopen(url_OEB)
    # Store the tool information in this variable
    data_json = json.loads(response.read())
    
    counter = 0 # Dummy counter
    # Initialize list variable for Programming Languages and Operative Systems
    l_languages = []
    l_os = []
    l_typetool=[]
    
    # Create MetaCitations table - It will be used to store Tools-Citations relationships
    # id1: Id of an article or the name of a Tool from OpenEBench
    # id2: Id of an article or the name of a Tool from OpenEBench
    # n_citations: Number of times the relationship between id1 and id2 is found
    # year: Year when the relationship occur
    c.execute('''DROP TABLE IF EXISTS MetaCitations''')
    c.execute('''CREATE TABLE MetaCitations AS
                select id1,id2, n_citations, year
                from Citations
            ''')
    
    # SQL Query for: Selecting Article IDs from the Publications table that are also found in table Citations
    c.execute("""SELECT p.doi, p.pmid
                    from Publications as p
                    INNER JOIN Citations as c ON
                    p.pmid == c.id1
                    union
                    SELECT p.doi, p.pmid
                    from Publications as p
                    INNER JOIN Citations as c ON
                    p.pmid == c.id2
                """)
    # Variable for all the articles found in the previous SQL Query
    publications=c.fetchall()
    
    # For each article
    for i in publications:
        counter += 1
        #print(counter)
        
        if not i[0]:
            doi = "None"
        else:
            doi = i[0]
        if not i[1]:
            pmid = "None"
        else:
            pmid = i[1]
        
        # Input the different IDs of the articles (DOI, PMID) to a function that retrieves all the tool information
        name_tool, label, typeTools, languages, operative_systems, list_keywords= search_json(data_json, doi, pmid)
        
        #print(name_tool,label, doi, pmid)
        # If the name of the tool is not found, try the next publication
        if not name_tool or not label:
            continue
        
        # If the tool is found, we can store it in the database
        c.execute(f"""INSERT OR IGNORE INTO Tools
                        values ('{name_tool}', '{label}')""")
        
        # If the tool has Type of software information
        if typeTools:
            # Store the languages in the database
            for typeTool in typeTools:
                if typeTool not in l_typetool:
                    # Insert to the table with all the Programming languages
                    c.execute(f"""INSERT INTO TypeTool
                                VALUES ('{typeTool}')""")
                    l_typetool.append(typeTool)
                # Insert the relationships between Tools and Languages
                c.execute(f"""INSERT OR IGNORE INTO ToolsToTypeTool
                            VALUES ('{typeTool}', '{label}')""")
        # If the tool has Programming Language information
        if languages:
            # Store the languages in the database
            for language in languages:
                if language not in l_languages:
                    # Insert to the table with all the Programming languages
                    c.execute(f"""INSERT INTO Languages
                                VALUES ('{language}')""")
                    l_languages.append(language)
                # Insert the relationships between Tools and Languages
                c.execute(f"""INSERT OR IGNORE INTO ToolsToLanguages
                            VALUES ('{language}', '{label}')""")
        # If the tool has Operative System information
        if operative_systems:
            # Store the OS in the database
            for op_sys in operative_systems:
                if op_sys not in l_os:
                    # Insert to the table with all the OS
                    c.execute(f"""INSERT INTO OperativeSystems
                                VALUES ('{op_sys}')""")
                    l_os.append(op_sys)
                # Insert the relationships between Tools and OS
                c.execute(f"""INSERT OR IGNORE INTO ToolsToOS
                            VALUES ('{op_sys}', '{label}')""")
        # If the tool has EDAM keywords, store them by type of keyword            
        if list_keywords:
            for typeKeyword, keywords in list_keywords.items():
                insert_keywords(label, keywords, typeKeyword)
            
                
        # Store the relationship between article and the tool that it describes with the information from OpenEBench
        c.execute(f'''INSERT INTO ToolsToPublications
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
