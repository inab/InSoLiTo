# Import libraries
import requests
import xml.etree.ElementTree as ET
import sys
from csv import reader

# Retrieve reference IDs from the Bibliography section
def retrieve_citations(section, set_references):
    for j in section.iter('xref'):
        if j.attrib['ref-type'] == "bibr" or j.attrib['ref-type'] == "ref":
            set_references.add(j.attrib['rid'])

# Search in methods and results section the references
def parse_publication(root, set_references):
    for body in root.iter('body'):
        for child in body.iter('sec'):
            if "sec-type" in child.attrib:
                if "methods" in child.attrib["sec-type"] :
                    retrieve_citations(child, set_references)
                if "results" in child.attrib["sec-type"] :
                    retrieve_citations(child, set_references)                    
            if child[0].text == "Results":
                retrieve_citations(child, set_references)          
    # Retrieve all the reference IDs with the type of ID (pmid, doi, pmcid)
    list_references = []
    for ref in root.iter('ref'):
        if ref.attrib['id'] in set_references:
            for id in ref.iter("pub-id"):
                list_references.append([[id.attrib["pub-id-type"], id.text]for id in ref.iter("pub-id")])
    print(list_references)


def main():
    with open(sys.argv[1]) as f:
        f = reader(f)
        count = 0
        for line in f:
            count += 1
            print(count)
            # Take the pmcid of each publication to search it in the API
            pmcid = line[3]
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
            print(pmcid)
            set_references = set()
            parse_publication(root, set_references)

if __name__ == '__main__':
    main()
