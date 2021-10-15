# Import libraries
from neo4j import GraphDatabase


# Import functions
from PublicationsNodes import create_publications_nodes
from ToolRelatedNodes import create_tools_nodes
from CitationsEdges import citations_edges
from DataScience import add_clusters_pageRank_Database

# URL of the Neo4j Server
uri = "bolt://localhost:7687"
# Driver to connect to the Server with the author and the password
# To be able to use it, you need to open your neo4j server before
driver = GraphDatabase.driver(uri, auth=("neo4j", ""))

def main():
    create_publications_nodes(driver)
    create_tools_nodes(driver)
    citations_edges(driver)
    add_clusters_pageRank_Database(driver)


if __name__ == '__main__':
    main()
