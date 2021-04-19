# Import libraries
import requests
import xml.etree.ElementTree as ET
import sys
import sqlite3
import time
from csv import reader
from os import walk
import itertools
import gzip
import io


# Start time - Just to count how much the script lasts
start_time = time.time()

# Name of the database
DB_FILE = "database/OAComparative.db"

# Connect to the SQLite database
# If name not found, it will create a new database
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Retrieve reference IDs from the Bibliography section
def retrieve_citations_labels(section, set_references):
    for j in section.iter('xref'):
        try:
            if j.attrib['ref-type'] in ["ref", "bibr"]:
                set_references.add(j.attrib['rid'])
        except:
            continue
            
def extract_references(set_references, label,id_pub1, year, dict_refs):
    references_list = []
    for i in set_references:
        if i in dict_refs:
            references_list.append(dict_refs[i])
    # Compute all possible combinations
    pos_comb = [subset for subset in itertools.combinations(references_list,2)]
    # Insert the citations in the database
    for comb in pos_comb:
        c.execute(f'''
                INSERT INTO Citations_{label}
                VALUES ("{comb[0]}", "{comb[1]}", 1, {year}, '{id_pub1}')
                ''')
    conn.commit()        

def search_references(root, set_all_sections):
    # Retrieve all the reference IDs with the type of ID (pmid, doi, pmcid)
    dict_references = {}
    for back in root.iter('back'):
        for ref_list in back.iter('ref-list'):
            for ref in ref_list.iter('ref'):
                if ref.attrib['id'] not in set_all_sections:
                    continue
                for element_citation in ref.iter('element-citation'):
                    for ids_pub in element_citation.iter("pub-id"):
                        if ids_pub.attrib['pub-id-type'] not in ["pmid", "pmcid", "doi"]:
                            continue
                        c.execute(f"""
                            SELECT id
                            FROM Publications
                            WHERE {ids_pub.attrib['pub-id-type']} = '{ids_pub.text}'
                            """)
                        id_pub2=c.fetchall()
                        if not id_pub2:
                            continue
                        for possible_id in id_pub2:
                            dict_references[ref.attrib['id']] = possible_id[0]
                        break
    return dict_references
    

# Search in methods and results section the references
def parse_publication(root,id_pub, year):
    set_introduction = set()
    set_methods = set()
    set_results = set()
    set_discussion = set()
    
    for body in root.iter('body'):
        for child in body.iter('sec'):
            if "sec-type" in child.attrib:
                if "intro" in child.attrib["sec-type"] :
                    retrieve_citations_labels(child, set_results)
                if "methods" in child.attrib["sec-type"] :
                    retrieve_citations_labels(child, set_methods)
                if "results" in child.attrib["sec-type"] :
                    retrieve_citations_labels(child, set_results)
                if "discussion" in child.attrib["sec-type"] :
                    retrieve_citations_labels(child, set_results)
            if child[0].text:
                if not set_introduction:
                    if "Introduction" in child[0].text:
                        retrieve_citations_labels(child, set_introduction)
                if not set_methods:
                    if "Methods" in child[0].text:
                        retrieve_citations_labels(child, set_methods)
                if not set_results:
                    if "Results" in child[0].text:
                        retrieve_citations_labels(child, set_results)
                if not set_discussion:
                    if "Discussion" in child[0].text:
                        retrieve_citations_labels(child, set_discussion)
    
    # Search references and extract their id
    set_all_sections = set_introduction | set_methods | set_results | set_discussion # Unify sets
    dict_refs = search_references( root, set_all_sections)
    
    extract_references(set_introduction, "Introduction",id_pub, year, dict_refs)
    extract_references(set_methods, "Methods", id_pub, year, dict_refs)
    extract_references(set_results, "Results", id_pub, year, dict_refs)
    extract_references(set_discussion, "Discussion",id_pub, year, dict_refs)
    conn.commit()


def main():
    OA_url = requests.get("https://europepmc.org/ftp/oa/pmcid.txt.gz")
    gz_file = OA_url.content
    f = io.BytesIO(gz_file)
    with gzip.GzipFile(fileobj=f) as OA_files:
        print("Updating possible OA publications")
        for OA_file in OA_files:
            c.execute(f'''
                INSERT OR IGNORE INTO OA_Publications
                VALUES ("{str(OA_file[:-1],'utf-8')}")
                ''')
        print("OA publications table done.")
        conn.commit()
    with open("SoLiTo/OpenAccessGraph/CreateSQLDatabase/OA_cache.txt") as OA_cache:
        print("Updating cache")
        for OA_cache_file in OA_cache:
            if not OA_cache_file:
                continue
            pmcid_pub, database = OA_cache_file.split() 
            c.execute(f'''
                INSERT OR IGNORE INTO OA_Cache
                VALUES ("{pmcid_pub}", "{database}")
                ''')
        conn.commit()        
    cache_file = open("SoLiTo/OpenAccessGraph/CreateSQLDatabase/OA_cache.txt", "a")
    # Select all publications
    c.execute("""
        SELECT pmcid, id, year
        FROM Publications
        """)
    publications=c.fetchall()
    count_open_pub = 0
    count = 0
    for publication in publications:
        count += 1
        print(count)
        # Take the pmcid of each publication to search it in the API
        pmcid = publication[0]
        id_pub = publication[1]
        c.execute(f"""
            SELECT PMCID, Database
            FROM OA_Cache
            WHERE PMCID = '{pmcid}'
            """)
        is_pub_in_another_database=c.fetchall()
        if is_pub_in_another_database:
            print("Pub already in cache")
            count_open_pub += 1
            for database_pub in is_pub_in_another_database:
                database = database_pub[1]
            if database == DB_FILE:
                print("Pub information already in database")
                continue
                
            c.execute(f"ATTACH DATABASE '{database}' AS other")
            
            list_sections = ["Introduction", "Methods", "Results","Discussion"]
            for sections in list_sections:
                c.execute(f"""
                        INSERT INTO Citations_{sections}
                        (id1, id2, n_citations, year, id_pub)
                        SELECT id1, id2, n_citations, year, id_pub
                        FROM other.Citations_{sections}
                        WHERE id_pub== {id_pub};""")
            conn.commit()        

        else:        
            c.execute(f"""
                SELECT PMCID
                FROM OA_Publications
                WHERE PMCID = '{pmcid}'
                """)
            is_OA=c.fetchall()
            if not is_OA:
                continue
            id_pub = publication[1]
            year = publication[2]
            
            if pmcid == "None" or pmcid == "pmcid":
                continue
            # API query
            req = f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML'
            r = requests.get(req)
            if not r:
                continue
            root = ET.fromstring(r.content)
            if not root.findall('body'):
                continue
            print(req)
            count_open_pub += 1
            parse_publication(root,id_pub, year)
            cache_file.write(f"{pmcid}\t{DB_FILE}\n")
            conn.commit()
    cache_file.close()            
    print(count_open_pub)

if __name__ == '__main__':
    main()
    c.close()
    print("--- %s seconds ---" % (time.time() - start_time))

