# Import libraries
from neo4j import GraphDatabase
import time

# Start time - Just to count how much the script lasts
start_time = time.time()

# URL of the Neo4j Server
uri = "bolt://localhost:7687"
# Driver to connect to the Server with the author and the password
# To be able to use it, you need to open your neo4j server before
driver = GraphDatabase.driver(uri, auth=("neo4j", "1234"))

def graph():
    with driver.session() as session:
        # Delete all the previous graph
        session.run("""MATCH ()-[r]->() DELETE r""")
        session.run("""MATCH (r) DELETE r""")
        session.run("""DROP INDEX index_publications IF EXISTS""")
    
    # Create Publication nodes
    # :Publication: Label of the node
    # id: Primary key of publication
    # title: Title of publication
    # year: Year of publication
    # pmcid: PMCID of the publication
    # pmid: PMID of the publication
    # doi: DOI of the publication
    print("Creating Publications nodes")
    try:
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///Publications.csv" AS csv
            CREATE (:Publication {  id:csv.id,
                                    title:csv.title,
                                    subtitle: substring(csv.title,0,15) + "...",
                                    year:toInteger(csv.year),
                                    pmcid:csv.pmcid,
                                    pmid:csv.pmid,
                                    doi:csv.doi
                                    })
            """)
    except:
        print("----> Error creating Publications nodes")
    
    # Index for Publication nodes
    print("Creating Publications index")
    try:
        session.run("""
            CREATE INDEX index_publications FOR (n:Publication) ON (n.id)
            """)
    except:
        print("----> Error creating Publication index")

if __name__ == '__main__':
    graph()
    print("--- %s seconds ---" % (time.time() - start_time))
