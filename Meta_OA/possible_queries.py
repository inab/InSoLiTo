# Import libraries
from neo4j import GraphDatabase
import itertools
import sys

# URL of the Neo4j Server
uri = "bolt://localhost:7687"
# Driver to connect to the Server with the author and the password
# To be able to use it, you need to open your neo4j server before
driver = GraphDatabase.driver(uri, auth=("neo4j", "1234"))

def stats_graph():
    with driver.session() as session:
        
        # Overlapping topics. See which ones are subtopics of other topics
        # It can be used for all type of edges
        session.run("""
            match (i:InferedTool)-[:TOPIC]->(top)
            with {item:id(top), categories:collect(id(i))} AS userData
            with collect(userData) as data
            CALL gds.alpha.similarity.overlap.stream({data: data})
            YIELD item1, item2, count1, count2, intersection, similarity
            RETURN gds.util.asNode(item1).label AS from, gds.util.asNode(item2).label AS to,
                count1, count2, intersection, similarity
            ORDER BY similarity DESC
            """)
        # Overlapping communities between Methods and Results with co-occurrences > 10
        session.run("""
            match ()-[mm]-(i)-[:HAS_COMMUNITY]->(top)
            where (type(mm) = "METAOCCUR_RESULTS_ALL" or type(mm) = "METAOCCUR_METHODS_ALL") and  mm.times > 10
            with {item:id(top), categories:collect(id(i))} AS userData
            with collect(userData) as data
            CALL gds.alpha.similarity.overlap.stream({data: data})
            YIELD item1, item2, count1, count2, intersection, similarity
            with gds.util.asNode(item1).com_id AS from, gds.util.asNode(item1).from_section AS section1, gds.util.asNode(item2).com_id AS to,
            gds.util.asNode(item2).from_section AS section2,
                count1, count2, intersection, similarity
            where section1 <>section2 and count1 > 1
            RETURN distinct from,section1,to, section2,
                count1, count2, intersection, similarity
            ORDER BY intersection DESC, similarity DESC
            """)
        # Add languages to the communities
        session.run("""
            match (l:Language)<-[:USE_LANGUAGE]-(i:InferedTool)-[:HAS_COMMUNITY]->(c:Community)
            where c.from_section="All"
            with c,l,count(i) as counti
            order by counti DESC
            with c,collect(l)[0] as mlanguage, max(counti) as maxcount
            set c.mlanguage=mlanguage.name, c.clanguage=id(mlanguage)
            return c,mlanguage, maxcount
            """)
        # Visualize communitites with languages
        session.run("""
            match (c1:Community)-[q:METAOCCUR_COMM]->(c2:Community)
            where c1.from_section="All" and c2.from_section="All" and (c1)<-[:HAS_COMMUNITY]-(:InferedTool)-[:USE_LANGUAGE]->(:Language) and (c2)<-[:HAS_COMMUNITY]-(:InferedTool)-[:USE_LANGUAGE]->(:Language)
            return c1,q,c2
            """)
        # Take 100 best nodes and show the relations between them
        session.run("""
             MATCH (i:InferedTool)-[o:METAOCCUR_ALL]->(p) WITH p,i, collect(o) as co UNWIND co as c WITH sum(c.times) as sumo, p,i, co ORDER BY sumo DESC with distinct i limit 100
            with collect(i) as ci
            unwind ci as i1
            unwind ci as i2
            match (i1)-[o:METAOCCUR_ALL]->(i2) WITH i1,i2, collect(o) as co UNWIND co as c WITH sum(c.times) as sumo, i1,i2, co return distinct i1, co, i2
            """)
        # Take 100 best nodes and extract all its relations with >50 co-occurrences
        session.run("""
            CALL{ MATCH (i:InferedTool)-[o:METAOCCUR]->(p) WITH p,i, collect(o) as co UNWIND co as c WITH sum(c.times) as sumo, p,i, co ORDER BY sumo DESC with distinct i limit 100 match (i)-[o:METAOCCUR]->(p) WITH p,i, collect(o) as co UNWIND co as c WITH sum(c.times) as sumo, p,i, co where sumo >=50 return distinct i,p,co, sumo } WITH i,co,p, sumo UNWIND co as c WITH i,p,sumo,c WHERE c.year = 2006 RETURN i,p,sumo,c
            """)
        # All the workflows from one InferedTool
        session.run("""
             MATCH (i:InferedTool)-[o:METAOCCUR_ALL]->(p) 
                where i.name="Comet" and o.times >0
                with distinct i, o, p  
                ORDER BY o.times DESC limit 100
                match (p)-[o2:METAOCCUR_METHODS_ALL]->(p2) 
                where o2.times >50
                return distinct i,o,p,o2,p2
            """)
        # All the workflows from a Topic
        session.run("""
            match (n:InferedTool)-[:TOPIC]->(k:Keyword)-[:SUBCLASS*]->(k2:Keyword)
                where k2.label="Proteomics" or k.label="Proteomics"
                with distinct n
                with collect(n) as nt
                unwind nt as nt1
                unwind nt as nt2
                match (nt1)-[m:METAOCCUR_ALL]-(nt2)
                return nt1,m,nt2
            """)
        ### Add topics in the communities
        # Empty topic for all the communities
        session.run("""
            MATCH (n:Community)
            set n.mtopic=NULL, n.ctopic=NULL
            return n.mtopic,n.ctopic
            """)
        # Topics for communities bigger than 1
        session.run("""
            MATCH (n:Community)-[h:METAOCCUR_COMM]-(q:Community)
            with n, collect(h) as ch
            where size(ch) >1
            with collect(n) as cn
            unwind cn as c
            with c
            Match (l:Keyword)<-[:TOPIC]-(i:InferedTool)-[:HAS_COMMUNITY]->(c)
            with c,l,count(i) as counti
            order by counti DESC
            with c,collect(l)[0] as mlanguage, max(counti) as maxcount
            set c.mtopic=mlanguage.label, c.ctopic=id(mlanguage)
            return c,mlanguage, maxcount
            """)
        # Query to retrieve relations between communities with topics and size >1
        session.run("""
            MATCH (n:Community)-[h:HAS_COMMUNITY]-(q)
            with n, collect(h) as ch
            where size(ch) >1 and n.ctopic is not null
            with collect(n) as cn
            unwind cn as c1
            unwind cn as c2
            Match (c1)-[w:METAOCCUR_COMM]->(c2)
            RETURN c1,w,c2
            """)
        
        ### Add languages in the communities
        # Empty language for all the communities
        session.run("""
            MATCH (n:Community)
            set n.mlanguage=NULL, n.clanguage=NULL
            return n.mtopic,n.ctopic
            """)
        # Languages for communities bigger than 1
        session.run("""
            MATCH (n:Community)-[h:METAOCCUR_COMM]-(q:Community)
            with n, collect(h) as ch
            where size(ch) >1
            with collect(n) as cn
            unwind cn as c
            with c
            Match (l:Language)<-[:USE_LANGUAGE]-(i:InferedTool)-[:HAS_COMMUNITY]->(c)
            with c,l,count(i) as counti
            order by counti DESC
            with c,collect(l)[0] as mlanguage, max(counti) as maxcount
            set c.mlanguage=mlanguage.name, c.clanguage=id(mlanguage)
            return c,mlanguage, maxcount
            """)
        # Query to retrieve relations between communities with languages and size >1
        session.run("""
            MATCH (n:Community)-[h:HAS_COMMUNITY]-(q)
            with n, collect(h) as ch
            where size(ch) >1 and n.clanguage is not null
            with collect(n) as cn
            unwind cn as c1
            unwind cn as c2
            Match (c1)-[w:METAOCCUR_COMM]->(c2)
            RETURN c1,w,c2
            """)
        
        ### Add Operative system in the community
        # Empty OS for all the communities
        session.run("""
            MATCH (n:Community)
            set n.mos=NULL, n.cos=NULL
            return n.mtopic,n.ctopic
            """)
        # OS for communities bigger than 1
        session.run("""
            MATCH (n:Community)-[h:METAOCCUR_COMM]-(q:Community)
            with n, collect(h) as ch
            where size(ch) >1
            with collect(n) as cn
            unwind cn as c
            with c
            Match (l:OS)<-[:USE_OS]-(i:InferedTool)-[:HAS_COMMUNITY]->(c)
            with c,l,count(i) as counti
            order by counti DESC
            with c,collect(l)[0] as mlanguage, max(counti) as maxcount
            set c.mos=mlanguage.name, c.cos=id(mlanguage)
            return c,mlanguage, maxcount
            """)
        # Query to retrieve relations between communities with OS and size >1
        session.run("""
            MATCH (n:Community)-[h:HAS_COMMUNITY]-(q)
            with n, collect(h) as ch
            where size(ch) >1 and n.cos is not null and n.ctopic is not null
            with collect(n) as cn
            unwind cn as c1
            unwind cn as c2
            Match (c1)-[w:METAOCCUR_COMM]->(c2)
            RETURN c1,w,c2
            """)
        

if __name__ == '__main__':
    stats_graph()
