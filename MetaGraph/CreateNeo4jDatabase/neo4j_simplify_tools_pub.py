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
    
        # Sum all co-occurences from the publications of the version of the tool to a concrete publication
        print("Sum co-occurences from the different version of tool to a publication")
        try:
            session.run("""
                MATCH (t:Tool)-[h:HAS_TOOL]-(p:Publication)-[o:OCCUR]-(p2:Publication)
                WITH t,collect(p) as collpub, COLLECT(o) as oldRels, SUM(o.times) as W, p2 , o.year as oyear
                foreach (oc IN oldRels |
                    foreach(pub in collpub |
                        merge (pub)-[oc:OCCUR {times:W, year:oyear}]-(p2)
                ))
                return *
                """)
        except:
            print("----> Error creating the sum of co-occurences")

        #Delete the edges that are not the sum of all the co-occurences from the different version of the tool to a publication
        print("Simplifying edges")
        try:
            session.run("""
                MATCH (t:Tool)-[h:HAS_TOOL]-(p:Publication)-[o:OCCUR]-(p2:Publication)
                WITH t,p, collect(o) as colo, p2, o.year as oyear
                where  size(colo)>1
                unwind colo as co
                with t,p,min(co.times) as c, p2, oyear
                Match (t:Tool)-[h:HAS_TOOL]-(p:Publication)-[o:OCCUR]-(p2:Publication)
                WITH t,p, collect(o) as colo, p2, o.year as oyear, c
                where  size(colo)>1
                unwind colo as co
                with t,p,co, p2, oyear, c
                where co.times = c
                delete co
                """)
        except:
            print("----> Error when Simplifying edges")

        #Collapse all the publications of the versions of a tool in a single node
        # Now, the function apoc.refactor.mergeNodes doesn't work well because when there are
        # two values of times equals, it stores only one value and not both of them. 
        print("Collapse all the publications of the versions into a single node")
        try:
            session.run("""
                MATCH (t:Tool)-[h:HAS_TOOL]-(p:Publication)
                WITH collect(p) as nodes, t
                where size(nodes) >1
                CALL apoc.refactor.mergeNodes(nodes,{properties:"combine", mergeRels:true})
                YIELD node
                RETURN count(*)
                """)
        except:
            print("----> Error collapsing all the publication versions")
            
        # Make an edge for each value of the list year and times from the collapsed edge
        print("Creating edges from the values of the collapsed edge")
        try:
            session.run("""
                MATCH (t:Tool)-[h:HAS_TOOL]-(p:Publication)-[o:OCCUR]-(p2:Publication)
                WITH t,p, o, p2, o.year as oyear, o.times as otimes
                foreach (i IN range(0,size(oyear)-1) |
                            merge (p)-[o:OCCUR {times:otimes[i], year: oyear[i]}]-(p2))
                return *
                """)
        except:
            print("----> Error Creating edges from the values of the collapsed edge")
        
        # Remove edge with more than one value in their times or year list
        print("Removing collapsed edge")
        try:
            session.run("""
                MATCH (t:Tool)-[h:HAS_TOOL]-(p:Publication)-[o:OCCUR]-(p2:Publication)
                where size(o.times) >1
                delete o
                """)
        except:
            print("----> Error collapsing all the publication versions")

if __name__ == '__main__':
    graph()
    print("--- %s seconds ---" % (time.time() - start_time))
