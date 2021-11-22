# Import libraries
import json
import itertools
from os import walk


def calculate_citations(mypath,c,conn):
    
    c.execute("""
            select id
            from UpdatePublications
        """)
    new_publications=c.fetchall()
    new_publications=[x[0] for x in new_publications]
    

    counter = 0 # Dummy counterd
    _, dirnames, _ = next(walk(mypath))

    for folder in dirnames:
        if not folder.startswith("pubs_"): # Only take folders with publications
            continue
        _, _, filenames = next(walk(f"{mypath}/{folder}/"))
        # For each file in folder
        for files in filenames:
            json_file = f"{mypath}/{folder}/{files}"
            
            traffic = json.load(open(json_file)) # Open JSON of each publication
            
            # If the publication is not new, we pass
            # We only want to compute the cooccurrences from the new publications
            if traffic["id"] not in new_publications:
                continue
            
            if "title" not in traffic:
                continue
            title = traffic["title"].replace('"', "'") # Standarize the quotation marks

            # Retrieve IDs
            l = [i["id"]for i in traffic["reference_refs"] if i["id"]]
            if "year" not in traffic:
                continue
            
            # Compute all possible combinations
            pos_comb = [subset for subset in itertools.combinations(l,2)]
            
            # Insert the citations in the database
            for comb in pos_comb:
                c.execute(f'''
                        INSERT INTO Citations (id1, id2, n_citations, year)
                        VALUES ("{comb[0]}", "{comb[1]}", 1, {traffic["year"]})
                        ''')
            counter+=1
            print(counter)
        conn.commit()
        if (counter%20000)==0:
            # Sum all the citations with the same values
            # The sum must be > 1 to store it in the database
            c.execute("""
                CREATE TABLE Citations_backup AS
                Select id1,id2, sum(n_citations) as n_citations, year
                from Citations
                group by id1, id2, year
                """)
            # We drop the table and then change the name to update the table
            c.execute("""DROP TABLE Citations""")
            c.execute("""
                ALTER TABLE Citations_backup
                RENAME TO Citations;
                """)
            conn.commit()
    # When the process is finished, store the Publication-Publication edges with more than 10 citations
    c.execute("""
        CREATE TABLE Citations_backup AS
        Select id1,id2, sum(n_citations) as n_citations, year
        from Citations
        group by id1, id2, year
        """)
    c.execute("""DROP TABLE Citations""")
    c.execute("""
        ALTER TABLE Citations_backup
        RENAME TO Citations;
        """)
    
    c.execute("""
        CREATE TABLE Citations_backup AS
        Select id1,id2, n_citations, year
        from Citations
        group by id1, id2, year
        HAVING n_citations > 10
        """)
    c.execute("""DROP TABLE Citations""")
    c.execute("""
        ALTER TABLE Citations_backup
        RENAME TO Citations;
        """)
