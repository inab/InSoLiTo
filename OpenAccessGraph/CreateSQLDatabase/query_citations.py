# Import libraries
import requests
import xml.etree.ElementTree as ET
import sys
import sqlite3
import time
from csv import reader
from os import walk
import itertools


# Start time - Just to count how much the script lasts
start_time = time.time()

# Name of the database
DB_FILE = "database/OAMolecular.db"

# Connect to the SQLite database
# If name not found, it will create a new database
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()


# Create Citations for the introduction section table
c.execute('''DROP TABLE IF EXISTS Citations_Introduction''')
c.execute('''CREATE TABLE "Citations_Introduction" (
                "id1"	TEXT NOT NULL,
                "id2"	TEXT NOT NULL,
                "n_citations" INTEGER,
                "year" INTEGER,
                FOREIGN KEY("id1") REFERENCES "Publications"("id"),
                FOREIGN KEY("id2") REFERENCES "Publications"("id")
            );''')

# Create Citations for the introduction section table
c.execute('''DROP TABLE IF EXISTS Citations_Methods''')
c.execute('''CREATE TABLE "Citations_Methods" (
                "id1"	TEXT NOT NULL,
                "id2"	TEXT NOT NULL,
                "n_citations" INTEGER,
                "year" INTEGER,
                FOREIGN KEY("id1") REFERENCES "Publications"("id"),
                FOREIGN KEY("id2") REFERENCES "Publications"("id")
            );''')

# Create Citations for the introduction section table
c.execute('''DROP TABLE IF EXISTS Citations_Results''')
c.execute('''CREATE TABLE "Citations_Results" (
                "id1"	TEXT NOT NULL,
                "id2"	TEXT NOT NULL,
                "n_citations" INTEGER,
                "year" INTEGER,
                FOREIGN KEY("id1") REFERENCES "Publications"("id"),
                FOREIGN KEY("id2") REFERENCES "Publications"("id")
            );''')

# Create Citations for the introduction section table
c.execute('''DROP TABLE IF EXISTS Citations_Discussion''')
c.execute('''CREATE TABLE "Citations_Discussion" (
                "id1"	TEXT NOT NULL,
                "id2"	TEXT NOT NULL,
                "n_citations" INTEGER,
                "year" INTEGER,
                FOREIGN KEY("id1") REFERENCES "Publications"("id"),
                FOREIGN KEY("id2") REFERENCES "Publications"("id")
            );''')


# Retrieve reference IDs from the Bibliography section
def retrieve_citations_labels(section, set_references):
    for j in section.iter('xref'):
        try:
            if j.attrib['ref-type'] in ["ref", "bibr"]:
                set_references.add(j.attrib['rid'])
        except:
            continue
            
def extract_references(root, set_references, label,id_pub1, year):
    # Retrieve all the reference IDs with the type of ID (pmid, doi, pmcid)
    references_list = set()
    for ref in root.iter('ref'):
        if ref.attrib['id'] in set_references:
            for ids_pub in ref.iter("pub-id"):
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
                    references_list.add(possible_id[0])
                break
    # Compute all possible combinations
    pos_comb = [subset for subset in itertools.combinations(references_list,2)]
    
    # Insert the citations in the database
    for comb in pos_comb:
        c.execute(f'''
                INSERT INTO Citations_{label}
                VALUES ("{comb[0]}", "{comb[1]}", 1, {year})
                ''')
    

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
            
    extract_references(root, set_introduction, "Introduction",id_pub, year)
    extract_references(root, set_methods, "Methods", id_pub, year)
    extract_references(root, set_results, "Results", id_pub, year)
    extract_references(root, set_discussion, "Discussion",id_pub, year)
    conn.commit()


def main():
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
    print(count_open_pub)

if __name__ == '__main__':
    main()
    c.close()
    print("--- %s seconds ---" % (time.time() - start_time))

