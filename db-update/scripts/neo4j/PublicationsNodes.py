
def create_publications_nodes(driver, PublicationsFile):
    """
    Create the Publication nodes in the graph database and an index for them.

    The Publications nodes are created from the CSV file specified in the input parameter.
    The node properties are:
    - id: Primary key of publication
    - title: Title of publication
    - year: Year of publication
    - pmcid: PMCID of the publication
    - pmid: PMID of the publication
    - doi: DOI of the publication

    An index is created for the Publication nodes on the pmid property.

    Parameters
    ----------
    driver : neo4j.Driver
        The driver to connect to the graph database.
    PublicationsFile : str
        The path to the CSV file containing the publication information.
    """
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
                LOAD CSV WITH HEADERS FROM "file:///%s" AS csv
                CREATE (:Publication {  title:csv.title,
                                        subtitle: substring(csv.title,0,15) + "...",
                                        year:toInteger(csv.year),
                                        pmcid:csv.pmcid,
                                        pmid:csv.pmid,
                                        doi:csv.doi
                                        })
                """ % (PublicationsFile))
        
        # Index for Publication nodes
        print("Creating Publications index")
        session.run("""
                CREATE INDEX index_publications FOR (n:Publication) ON (n.pmid)
                """)

