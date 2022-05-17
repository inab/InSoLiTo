import sys
import gzip
import xml.etree.ElementTree as ET
import itertools



import sqlite3

file_xml = sys.argv[1]

# Name of the database
DB_FILE = f"{sys.argv[2]}.db"

# Connect to the SQLite database
# If name not found, it will create a new database
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()




with gzip.open(file_xml,"r") as f:
    root = ET.parse(f)
       
    for article in root.iter("PubmedArticle"):
        has_references = False
        #Store the references in this dictionary
        dict_references = {"pmid":[], "doi":[], "pmcid":[]}
        
        # Gather all the references that have an Article Id
        # Only take one Id of each reference. Order: pmid > doi > pmcid
        for references in article.iter("Reference"):
            # Initialize variables
            pmid_ref = ""
            doi_ref= ""
            pmcid_ref = ""
            for id_ref in references.iter("ArticleId"):
                has_references = True
                if "pubmed" in id_ref.attrib["IdType"]:
                    pmid_ref = id_ref.text 
                    # If we find a pubmed reference, stop looking for other ids
                    break                               
                if "doi" in id_ref.attrib["IdType"]:
                    doi_ref = id_ref.text
                if "pmcid" in id_ref.attrib["IdType"]:
                    pmcid_ref = id_ref.text
            if pmid_ref:
                dict_references["pmid"] += [pmid_ref]
            elif doi_ref:
                dict_references["doi"] += [doi_ref]
            elif pmcid_ref:
                dict_references["pmcid"] += [pmcid_ref]
                
        # If there are no references, continue to the next article
        if has_references == False:
            continue
        
        # Check if the references are in the Publications table of the database
        # Store them the following list
        list_ref_pub = []
        # If there is only one
        if (len(dict_references["pmid"]) + len(dict_references["doi"]) + len(dict_references["pmcid"])) < 2:
            continue
        for id_type in ["pmid","doi","pmcid"]:
            for ids_per_type in dict_references[id_type]:
                c.execute(f'''
                        SELECT pmid
                        FROM Publications
                        WHERE {id_type} = "{ids_per_type}"
                        LIMIT 1;
                        ''')
                isId=c.fetchall()
                if not isId:
                    continue
                #print(isId[0][0])
                list_ref_pub.append(isId[0][0])
        #print(list_ref_pub)
        if list_ref_pub and len(list_ref_pub)>1:
            #Compute all possible combinations
            pos_comb = [subset for subset in itertools.combinations(list_ref_pub,2)]
            print(pos_comb)
        
        for date_atr in article.iter("PubDate"):
            for year_atr in date_atr.iter("Year"):  
                year = year_atr.text
        
        #for articleId_atr in article.iter("ArticleIdList"):
            #for Id_atr in articleId_atr.iter("ArticleId"):
                #if "pubmed" in Id_atr.attrib["IdType"]:
                    #pubmed_id = Id_atr.text
                #if "doi" in Id_atr.attrib["IdType"]:
                    #doi_id = Id_atr.text
                #if "pmcid" in Id_atr.attrib["IdType"]:
                    #pmcid_id = Id_atr.text
            #break
        #print(title, year, pubmed_id, doi_id, pmcid_id, pubmed_ref, doi_ref, pmcid_ref)

        
