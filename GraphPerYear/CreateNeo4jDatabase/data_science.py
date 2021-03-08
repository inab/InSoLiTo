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
        ### PageRank
        # Creating the "view"
        session.run("""
            CALL gds.graph.create(
                'got-interactions', 
                'Publication', 
                {
                    OCCUR: 
                    {
                        orientation: 'UNDIRECTED'
                    }
                }
            )
            """)
        # Write PageRank values to each node
        session.run("""
            CALL gds.pageRank.write(
                'got-interactions', 
                {
                    writeProperty: 'pageRank'
                }
            )
            """)
        ### Louvain weighted
        # Create view with the property
        session.run("""
            CALL gds.graph.create(
            'got-weighted-interactions',
            'Publication',
            {
                OCCUR: {
                orientation: 'UNDIRECTED',
                aggregation: 'NONE',
                properties: {
                    times: {
                    property: 'times',
                    aggregation: 'NONE',
                    defaultValue: 0.0
                    }
                }
                }
            }
            )
            """)
        # Write the community id to each node
        session.run("""
            CALL gds.louvain.write(
            'got-weighted-interactions',
            {
                relationshipWeightProperty: 'times',
                writeProperty: 'community',

            }
            )
            """)


if __name__ == '__main__':
    graph()
    print("--- %s seconds ---" % (time.time() - start_time))
