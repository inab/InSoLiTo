# Import libraries
import json
from os import walk


def retrieve_publications(mypath,c):
    
    counter = 0 # Dummy counter
    
    _, dirnames, _ = next(walk(mypath))
    
    c.execute("PRAGMA max_page_count = 2147483646;")
    
    c.execute("""
        select id
        from Publications
        """)
    old_publications=c.fetchall()
    old_publications=set(x[0] for x in old_publications)


    #For each folder
    for folder in dirnames:
        if not folder.startswith("pubs_"): # Only take folders with publications
            continue
        _, _, filenames = next(walk(f"{mypath}/{folder}/"))
        #For each file inside the folder
        for files in filenames:
            json_file = f"{mypath}/{folder}/{files}"
            
            traffic = json.load(open(json_file)) # Open JSON of each publication
            if traffic["id"] in old_publications:
                continue
            if "title" not in traffic:
                continue
            title = traffic["title"].replace('"', "'") # Standarize the quotation marks
            #Insert Publication information into the database
            c.execute(f'''INSERT OR REPLACE INTO Publications
                        VALUES ("{traffic["id"]}","{title}",{traffic["year"]},"{traffic["pmcid"]}", "{traffic["pmid"]}", "{traffic["doi"]}")''')
            c.execute(f'''INSERT OR REPLACE INTO UpdatePublications
                        VALUES ("{traffic["id"]}","{title}",{traffic["year"]},"{traffic["pmcid"]}", "{traffic["pmid"]}", "{traffic["doi"]}")''')
            print(counter)
            counter+=1
    print(f"There are {counter} publications in the database")
