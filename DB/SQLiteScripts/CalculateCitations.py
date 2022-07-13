# Import libraries
import gzip
import itertools
import xml.etree.ElementTree as ET
from os import walk

# Function: Sum the "n_citations" when two equal relationships are found
def aggregate_citations(c, conn):
    print("aggregate")
    #Sum all the citations with the same values
    c.execute("""
        CREATE TABLE Citations_backup AS
        Select id1,id2, sum(n_citations) as n_citations, year
        from Citations
        group by id1, id2, year
        """)
    #We drop the table and then change the name to update the table
    c.execute("""DROP TABLE Citations""")
    c.execute("""
        ALTER TABLE Citations_backup
        RENAME TO Citations;
        """)
    conn.commit()

# Function: Remove all the relationships having less than "min_citations"
def truncate_citations(c,conn, min_citations):
    print("truncate")
    c.execute(f"""
        CREATE TABLE Citations_backup AS
        Select id1,id2, n_citations, year
        from Citations
        where n_citations > {min_citations}
        """)
    c.execute('''DROP TABLE Citations''')
    c.execute("""
        ALTER TABLE Citations_backup
        RENAME TO Citations;
        """)
    conn.commit()
    #Compact the database
    c.execute("VACUUM;")
    conn.commit()

# Main function
def calculate_citations(mypath,c,conn):

    counter = 0         # Dummy counter for publications
    counter_files = 0   # Dummy counter for files
    
    # Take all the files from the path
    _, _, filenames = next(walk(f"{mypath}/"))
    
    # For each file
    for files in filenames:
        filepath = f"{mypath}/{files}"
        # Not compressed files are not parsed (Ex: Index files)
        if not filepath.endswith("xml.gz"):
            continue
        # Open the gzip and do the calculations
        with gzip.open(filepath,"r") as f:
            print(f"Parsing {filepath}")
            # Read XML file
            root = ET.parse(f)
            # For all the publications in the file
            for article in root.iter("PubmedArticle"):
                # Variable created to see if the article has references
                has_references = False
                #Store the references in this dictionary
                dict_references = {"pmid":[], "doi":[]}
                
                # Gather all the references that have an Article Id
                # Only take one Id of each reference. Order: pmid > doi
                for references in article.iter("Reference"):
                    # Initialize variables
                    pmid_ref = ""
                    doi_ref= ""
                    for id_ref in references.iter("ArticleId"):
                        has_references = True
                        if "pubmed" in id_ref.attrib["IdType"]:
                            pmid_ref = id_ref.text 
                            # If we find a pubmed reference, stop looking for other ids
                            break                               
                        if "doi" in id_ref.attrib["IdType"]:
                            doi_ref = id_ref.text
                    # Store IDs in the dictionary
                    if pmid_ref:
                        dict_references["pmid"] += [pmid_ref]
                    elif doi_ref:
                        dict_references["doi"] += [doi_ref]

                        
                # If there are no references, continue to the next article
                if has_references == False:
                    continue
                # If there is only one reference, continue to the next article
                if (len(dict_references["pmid"]) + len(dict_references["doi"])) < 2:
                    continue
                
                # Store the references in the following list
                list_ref_pub = []
                # Convert the DOI into PMID with the database information
                # So, we have only one ID type in the Citations table of the database
                
                for ids_per_type in dict_references["doi"]:
                    # SQL Query that returns the PMID of the article from its DOI
                    c.execute(f'''
                            SELECT pmid
                            FROM Publications
                            WHERE doi = "{ids_per_type}"
                            LIMIT 1;
                            ''')
                    isId=c.fetchall()
                    # If no DOI found,try the next reference
                    if not isId:
                        continue
                    # Append the DOI from the SQL Query to the list
                    list_ref_pub.append(isId[0][0])
                # Append the DOI from the file
                for pub_id in dict_references["pmid"]:
                    # Checking that the ID come in the right format
                    if pub_id.isdigit():
                        list_ref_pub.append(pub_id)
                # If there are more than one reference in the list
                if len(list_ref_pub)>1:
                    #Compute all possible pair combinations
                    pos_comb = [subset for subset in itertools.combinations(list_ref_pub,2)]
                    
                # Search and store the year of publication
                for date_atr in article.iter("PubDate"):
                    for year_atr in date_atr.iter("Year"):  
                        year = year_atr.text
            
                #Insert the citations in the database
                for comb in pos_comb:
                    # Sort the Citations in the database, by putting the smaller IDs to the "id1" column
                    if int(comb[0]) > int(comb[1]):
                        # SQL Query for inserting the combinations of references in the Citations table
                        c.execute(f'''
                                INSERT INTO Citations (id1, id2, n_citations, year)
                                VALUES ("{comb[0]}", "{comb[1]}", 1, {year})
                                ''')
                    else:
                        c.execute(f'''
                                INSERT INTO Citations (id1, id2, n_citations, year)
                                VALUES ("{comb[1]}", "{comb[0]}", 1, {year})
                                ''')
                counter+=1
            # Add the data to the database
            conn.commit()
            # Sum all the possible combinations to the other combinations in the database            
            aggregate_citations(c, conn)
        counter_files += 1
        if (counter_files%10)==0:
            truncate_citations(c,conn, 1)
            
    # Sum all the final possible combinations to the other combinations in the database
    aggregate_citations(c, conn)
    
    #When the process is finished, store the Publication-Publication edges with more than 10 citations
    truncate_citations(c,conn, 10)
    print(counter, "publications with citations")
