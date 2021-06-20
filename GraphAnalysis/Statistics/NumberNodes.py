# Import libraries
from neo4j import GraphDatabase
import sys

# URL of the Neo4j Server
uri = "bolt://localhost:7687"
# Driver to connect to the Server with the author and the password
# To be able to use it, you need to open your neo4j server before
driver = GraphDatabase.driver(uri, auth=("neo4j", "1234"))

def stats_graph():
    with driver.session() as session:
                
        ########## Calculate number of nodes in a range of co-occurrences
        # Here, it queries the number of nodes from 10 to 1000co-occurrences
        number_of_nodes = open(sys.argv[1], "w")
        UseCaseName = sys.argv[2]
        number_of_nodes.write(f"Time\tTool\tPublication\tpercentage\tUsecase\n")
        
        for num_cor in range(10, 1000):
            percentage_tools = session.run("""
                Match (n:InferedTool)-[m:METAOCCUR_ALL]-()
                where m.times > %s
                with distinct n
                return count(n) as num_tools
            """ % (num_cor))
            
            percentage_publications = session.run("""
                Match (n:Publication)-[m:METAOCCUR_ALL]-()
                where m.times > %s
                with distinct n
                return count(n) as num_pubs
            """ % (num_cor))

            num_tools = percentage_tools.data()[0]["num_tools"]
            num_pubs = percentage_publications.data()[0]["num_pubs"]
            
            print(num_cor,num_tools, num_pubs,  num_tools/(num_tools + num_pubs))
            number_of_nodes.write(f"{num_cor}\t{num_tools}\t{num_pubs}\t{num_tools/(num_tools + num_pubs)}\t{UseCaseName}\n")
        
        number_of_nodes.close()

if __name__ == '__main__':
    stats_graph()
