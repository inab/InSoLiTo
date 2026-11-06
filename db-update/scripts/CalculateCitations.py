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
    # Threshold on the pair's total across years, so per-year rows of a frequent pair are kept
    c.execute("""
        CREATE TABLE Citations_backup AS
        Select id1,id2, n_citations, year
        from Citations
        where (id1, id2) in (
            select id1, id2 from Citations
            group by id1, id2
            having sum(n_citations) > ?
        )
        """, (min_citations,))
    c.execute('''DROP TABLE Citations''')
    c.execute("""
        ALTER TABLE Citations_backup
        RENAME TO Citations;
        """)
    conn.commit()
    #Compact the database
    c.execute("VACUUM;")
    conn.commit()

# PMIDs of the tools' own papers, the only pairs InferToolsKeywords keeps in the end
# DOIs are mapped to PMIDs with the Publications table, as InferToolsKeywords does
def get_tool_pmids(c, oeb_data):
    tool_pmids = set()
    for tool in oeb_data:
        for publication in tool.get("publications") or []:
            pmid = str(publication.get("pmid", ""))
            if pmid.isdigit():
                tool_pmids.add(pmid)
            elif "doi" in publication:
                c.execute("SELECT pmid FROM Publications WHERE doi = ? LIMIT 1", (publication["doi"],))
                row = c.fetchone()
                if row:
                    tool_pmids.add(str(row[0]))
    return tool_pmids

# DOIs of the tools' own papers, to skip the articles that cite no tool before looking up their DOIs
def get_tool_dois(c, tool_pmids):
    tool_dois = set()
    c.execute("SELECT pmid, doi FROM Publications WHERE doi IS NOT NULL")
    for pmid, doi in c:
        if str(pmid) in tool_pmids:
            tool_dois.add(doi)
    return tool_dois

# Main function
def calculate_citations(mypath,c,conn, oeb_data):

    tool_pmids = get_tool_pmids(c, oeb_data)
    print(f"{len(tool_pmids)} tool papers")
    tool_dois = get_tool_dois(c, tool_pmids)
    print(f"{len(tool_dois)} tool DOIs")

    counter = 0         # Dummy counter for publications
    
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
            # Read the XML one article at a time instead of loading the whole file into memory
            context = ET.iterparse(f, events=("start", "end"))
            _, root = next(context)
            # For all the publications in the file
            for event, article in context:
                if event != "end" or article.tag != "PubmedArticle":
                    continue
                # Free the articles already processed; the current one is kept by the "article" variable
                root.clear()
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
                # Skip articles that cite no tool paper: none of their pairs would be kept
                if not (any(p in tool_pmids for p in dict_references["pmid"])
                        or any(d in tool_dois for d in dict_references["doi"])):
                    continue
                
                # Store the references in the following list
                list_ref_pub = []
                # Convert the DOI into PMID with the database information
                # So, we have only one ID type in the Citations table of the database
                
                for ids_per_type in dict_references["doi"]:
                    # SQL Query that returns the PMID of the article from its DOI
                    # Parameter, not f-string: some DOIs contain quotes
                    c.execute("SELECT pmid FROM Publications WHERE doi = ? LIMIT 1", (ids_per_type,))
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
                # Reset per article: otherwise the previous article's pairs are inserted again
                pos_comb = []
                # If there are more than one reference in the list
                if len(list_ref_pub)>1:
                    #Compute all possible pair combinations
                    # Only pairs with a tool paper: the rest are dropped at the end anyway
                    pos_comb = [subset for subset in itertools.combinations(list_ref_pub,2)
                                if str(subset[0]) in tool_pmids or str(subset[1]) in tool_pmids]

                # Search and store the year of publication
                year = None
                for date_atr in article.iter("PubDate"):
                    for year_atr in date_atr.iter("Year"):
                        year = year_atr.text
                # Same rule as RetrievePublications: no year, no article
                if not year:
                    continue

                #Insert the citations in the database
                for comb in pos_comb:
                    # Sort the Citations in the database, by putting the smaller IDs to the "id1" column
                    if int(comb[0]) > int(comb[1]):
                        # SQL Query for inserting the combinations of references in the Citations table
                        c.execute("INSERT INTO Citations (id1, id2, n_citations, year) VALUES (?, ?, 1, ?)",
                                  (str(comb[0]), str(comb[1]), int(year)))
                    else:
                        c.execute("INSERT INTO Citations (id1, id2, n_citations, year) VALUES (?, ?, 1, ?)",
                                  (str(comb[1]), str(comb[0]), int(year)))
                counter+=1
            # Add the data to the database
            conn.commit()

    # Sum all the final possible combinations to the other combinations in the database
    aggregate_citations(c, conn)
    
    #When the process is finished, store the Publication-Publication edges with more than 10 citations
    truncate_citations(c,conn, 1)
    print(counter, "publications with citations")
