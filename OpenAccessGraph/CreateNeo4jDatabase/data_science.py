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
        # Remove nodes with no interactions
        session.run("""
            MATCH (n)
            WHERE size((n)--())=0
            DELETE (n)
            """)
        # Remove previous nodes and edges
        session.run("""MATCH ()-[r:METAOCCUR_COMM]->() DELETE r""")
        session.run("""MATCH ()-[r:HAS_COMMUNITY]->() DELETE r""")
        session.run("""MATCH (r:Community) DELETE r""")
        
        print("Creating methods view")
        
        ################################### Methods
        # Create view with the property
        session.run("""
            CALL gds.graph.create(
            'got-weighted-interactions',
            ['InferedTool', 'Publication'],
            {
                METAOCCUR_METHODS_ALL: {
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
        print("PageRank for methods")
        # Write PageRank values to each node
        session.run("""
            CALL gds.pageRank.write(
                'got-weighted-interactions', 
                {
                    relationshipWeightProperty: 'times',
                    writeProperty: 'pageRank'
                }
            )
            """)
        print("Louvain for methods")
        # Write the community id to each node
        session.run("""
            CALL gds.louvain.write(
                'got-weighted-interactions',
                {
                    relationshipWeightProperty: 'times',
                    writeProperty: 'community'
                }
            )
            """)
        
        print("Create clusters for methods")
        # Create clusters as nodes
        session.run("""
            MATCH (n) 
            WITH distinct n.community as com 
            CREATE (:Community {com_id: com, from_section: "Methods"})
            """)
        # Edges between nodes and its communities
        session.run("""
            MATCH (n),(i:Community) 
            WHERE n.community = i.com_id and i.from_section="Methods"
            CREATE (n)-[:HAS_COMMUNITY]->(i)
            """)
        session.run("""
            MATCH (c2:Community)<-[h2:HAS_COMMUNITY]-(p)-[m:METAOCCUR_METHODS_ALL]-(n)-[h:HAS_COMMUNITY]->(c1:Community)
            WHERE c1<> c2
            WITH c2,c1, collect(m) as co
                UNWIND co as c 
            WITH c2, sum(c.times) as sumo , c1
            CREATE (c1)-[:METAOCCUR_COMM {times: sumo}]->(c2)
            """)
        # Delete duplicated and reversed relationships
        session.run("""
            Match (c1:Community)-[r:METAOCCUR_COMM]->(c2:Community)
            where c1.com_id < c2.com_id
            delete r
            """)
        session.run("""
            CALL gds.graph.drop('got-weighted-interactions')
        """)
                
        ################################### Results
        
        print("Creating results view")

        # Create view with the property
        session.run("""
            CALL gds.graph.create(
            'got-weighted-interactions-res',
            ['InferedTool', 'Publication'],
            {
                METAOCCUR_RESULTS_ALL: {
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

        print("Louvain for results")
        # Write the community id to each node
        session.run("""
            CALL gds.louvain.write(
                'got-weighted-interactions-res',
                {
                    relationshipWeightProperty: 'times',
                    writeProperty: 'community_res'
                }
            )
            """)
        
        print("Create clusters for results")
        # Create clusters as nodes
        session.run("""
            MATCH (n) 
            WITH distinct n.community_res as com
            CREATE (:Community {com_id: com, from_section: "Results"})
            """)
        # Edges between nodes and its communities
        session.run("""
            MATCH (n),(i:Community) 
            WHERE n.community_res = i.com_id and i.from_section="Results"
            CREATE (n)-[:HAS_COMMUNITY]->(i)
            """)
        session.run("""
            MATCH (c2:Community)<-[h2:HAS_COMMUNITY]-(p)-[m:METAOCCUR_RESULTS_ALL]-(n)-[h:HAS_COMMUNITY]->(c1:Community)
            WHERE c1<> c2
            WITH c2,c1, collect(m) as co
                UNWIND co as c 
            WITH c2, sum(c.times) as sumo , c1
            CREATE (c1)-[:METAOCCUR_COMM {times: sumo}]->(c2)
            """)
        # Delete duplicated and reversed relationships
        session.run("""
            Match (c1:Community)-[r:METAOCCUR_COMM]->(c2:Community)
            where c1.com_id < c2.com_id
            delete r
            """)
        session.run("""
            CALL gds.graph.drop('got-weighted-interactions-res')
        """)


if __name__ == '__main__':
    graph()
    print("--- %s seconds ---" % (time.time() - start_time))
