# Import libraries
import gzip
import xml.etree.ElementTree as ET
from os import walk

def retrieve_publications(mypath,c):
    counter = 0 # Dummy counter
    
    # Take all the files from the path
    _, _, filenames = next(walk(f"{mypath}/"))
    
    # For each file
    for files in filenames:
        filepath = f"{mypath}/{files}"
        # Not compressed files are not parsed (Ex: Index files)
        if not filepath.endswith("xml.gz"):
            continue
        print("Parsing", filepath)
        # Open the gzip and do the calculations
        with gzip.open(filepath,"r") as f:
            # Read XML file
            root = ET.parse(f)
            # For all the publications in the file
            for article in root.iter("PubmedArticle"):
                # Initialize variables where the ids will be stored
                pubmed_id = None
                doi_id = None
                # Search and store the title
                for title_atr in article.iter("ArticleTitle"):
                    title = ''.join(title_atr.itertext())   # Take all text and the tags inside them
                    title = title.replace('"', "'")         # Standarize the quotation marks
                
                # If no title, do not store article
                if not title:
                    continue
                # Search and store the year of publication
                for date_atr in article.iter("PubDate"):
                    for year_atr in date_atr.iter("Year"):  
                        year = year_atr.text
                # If no year, do not store article
                if not year:
                    continue
                # Search and store the ID of the article
                # We only want the first <ArticleIdList>, because is the one having the Id of the article
                # The other <ArticleIdList> are for the references
                for articleId_atr in article.iter("ArticleIdList"):
                    for Id_atr in articleId_atr.iter("ArticleId"):
                        if "pubmed" in Id_atr.attrib["IdType"]:
                            pubmed_id = Id_atr.text
                        if "doi" in Id_atr.attrib["IdType"]:
                            doi_id = Id_atr.text
                    break
                # If article has any ID
                if not pubmed_id:
                    continue
                if doi_id:
                    #Insert the variables into the database, in the table Publications
                    c.execute(f'''INSERT OR REPLACE INTO Publications
                                VALUES ("{title}",{year}, {pubmed_id}, "{doi_id}")''')
                else:
                    #Insert the variables into the database, in the table Publications
                    c.execute(f'''INSERT OR REPLACE INTO Publications
                                VALUES ("{title}",{year}, {pubmed_id}, null)''')                    
                    counter+=1
    print(f"There are {counter} publications in the database")
