
def create_publications_nodes(driver, file_path, PublicationsFile):
    with driver.session() as session:
        print("Removing all data in the database")
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
        session.run("""
                LOAD CSV WITH HEADERS FROM "file:///%s%s" AS csv
                CREATE (:Publication {  title:csv.title,
                                        subtitle: substring(csv.title,0,15) + "...",
                                        year:toInteger(csv.year),
                                        pmcid:csv.pmcid,
                                        pmid:csv.pmid,
                                        doi:csv.doi
                                        })
                """ % (file_path,PublicationsFile))
        
        # Index for Publication nodes
        print("Creating Publications index")
        session.run("""
                CREATE INDEX index_publications FOR (n:Publication) ON (n.pmid)
                """)

