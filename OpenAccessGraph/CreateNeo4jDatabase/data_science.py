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
        
        list_labels = ["INTRODUCTION", "METHODS", "RESULTS", "DISCUSSION"]
        for label in list_labels:
        
            print(f"Creating {label} view")

            # Create view with the property
            session.run("""
                CALL gds.graph.create(
                'got-weighted-interactions-%s',
                ['InferedTool', 'Publication'],
                {
                    METAOCCUR_%s_ALL: {
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
                """ % (label, label))

            print(f"Louvain for {label}")
            # Write the community id to each node
            session.run("""
                CALL gds.louvain.write(
                    'got-weighted-interactions-%s',
                    {
                        relationshipWeightProperty: 'times',
                        writeProperty: 'community_%s'
                    }
                )
                """% (label, label))
            
            if label=="METHODS":
                print("PageRank for all dataset")
                # Write PageRank values to each node
                session.run("""
                    CALL gds.pageRank.write(
                        'got-weighted-interactions-%s', 
                        {
                            relationshipWeightProperty: 'times',
                            writeProperty: 'pageRank'
                        }
                    )
                    """% (label))
            
            session.run("""
                CALL gds.graph.drop('got-weighted-interactions-%s')
            """% (label))

############################ Create Community nodes ####################################
        list_edges_names = ["_INTRODUCTION", "_METHODS", "_RESULTS", "_DISCUSSION"]
        list_labels = ["Introduction", "Methods", "Results", "Discussion"]
        
        for label in range(len(list_edges_names)):

            print("Create clusters for all dataset")
            # Create clusters as nodes
            session.run("""
                MATCH (n) 
                WITH distinct n.community%s as com
                CREATE (:Community {com_id: com, from_section: "%s"})
                """ % (list_edges_names[label], list_labels[label]))
            # Edges between nodes and its communities
            session.run("""
                MATCH (n),(i:Community) 
                WHERE n.community%s = i.com_id and i.from_section="%s"
                CREATE (n)-[:HAS_COMMUNITY]->(i)
                """ % (list_edges_names[label], list_labels[label]))
            session.run("""
                MATCH (c2:Community)<-[h2:HAS_COMMUNITY]-(p)-[m:METAOCCUR%s_ALL]-(n)-[h:HAS_COMMUNITY]->(c1:Community)
                WHERE c1<> c2 and c1.from_section="%s" and c2.from_section="%s"
                WITH c2,c1, collect(m) as co
                    UNWIND co as c 
                WITH c2, sum(c.times) as sumo , c1
                CREATE (c1)-[:METAOCCUR_COMM {times: sumo}]->(c2)
                """ % (list_edges_names[label], list_labels[label], list_labels[label]))
            # Delete duplicated and reversed relationships
            session.run("""
                Match (c1:Community)-[r:METAOCCUR_COMM]->(c2:Community)
                where c1.com_id < c2.com_id
                delete r
                """)

            #################### Create community properties #######################
        
            ### Add most common topics in the communities
            # Empty topic for all the communities
            session.run("""
                MATCH (n:Community)
                where i.from_section="%s"
                set n.mtopic=NULL, n.ctopic=NULL
                return n.mtopic,n.ctopic
                """ % (list_labels[label]))
            # Topics for communities bigger than 1
            session.run("""
                MATCH (n:Community)-[h:METAOCCUR_COMM]-(q:Community)
                with n, collect(h) as ch
                where size(ch) >1 and n.from_section="%s" and q.from_section="%s"
                with collect(n) as cn
                unwind cn as c
                with c
                Match (l:Keyword)<-[:TOPIC]-(i:InferedTool)-[:HAS_COMMUNITY]->(c)
                with c,l,count(i) as counti
                order by counti DESC
                with c,collect(l)[0] as mlanguage, max(counti) as maxcount
                set c.mtopic=mlanguage.label, c.ctopic=id(mlanguage)
                return c,mlanguage, maxcount
                """ % (list_labels[label], list_labels[label]))
            ### Add most common languages in the communities
            # Empty language for all the communities
            session.run("""
                MATCH (n:Community)
                where i.from_section="%s"
                set n.mlanguage=NULL, n.clanguage=NULL
                return n.mtopic,n.ctopic
                """ % (list_labels[label]))
            # Languages for communities bigger than 1
            session.run("""
                MATCH (n:Community)-[h:METAOCCUR_COMM]-(q:Community)
                with n, collect(h) as ch
                where size(ch) >1 and n.from_section="%s" and q.from_section="%s"
                with collect(n) as cn
                unwind cn as c
                with c
                Match (l:Language)<-[:USE_LANGUAGE]-(i:InferedTool)-[:HAS_COMMUNITY]->(c)
                with c,l,count(i) as counti
                order by counti DESC
                with c,collect(l)[0] as mlanguage, max(counti) as maxcount
                set c.mlanguage=mlanguage.name, c.clanguage=id(mlanguage)
                return c,mlanguage, maxcount
                """ % (list_labels[label], list_labels[label]))
            ### Add most common Operative system in the community
            # Empty OS for all the communities
            session.run("""
                MATCH (n:Community)
                where i.from_section="%s"                
                set n.mos=NULL, n.cos=NULL
                return n.mtopic,n.ctopic
                """ % (list_labels[label]))
            # OS for communities bigger than 1
            session.run("""
                MATCH (n:Community)-[h:METAOCCUR_COMM]-(q:Community)
                with n, collect(h) as ch
                where size(ch) >1 and n.from_section="%s" and q.from_section="%s"
                with collect(n) as cn
                unwind cn as c
                with c
                Match (l:OS)<-[:USE_OS]-(i:InferedTool)-[:HAS_COMMUNITY]->(c)
                with c,l,count(i) as counti
                order by counti DESC
                with c,collect(l)[0] as mlanguage, max(counti) as maxcount
                set c.mos=mlanguage.name, c.cos=id(mlanguage)
                return c,mlanguage, maxcount
                """ % (list_labels[label], list_labels[label]))

if __name__ == '__main__':
    graph()
    print("--- %s seconds ---" % (time.time() - start_time))
