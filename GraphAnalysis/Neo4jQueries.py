# Import libraries
from neo4j import GraphDatabase
import itertools
import sys

# URL of the Neo4j Server
uri = "bolt://localhost:7687"
# Driver to connect to the Server with the author and the password
# To be able to use it, you need to open your neo4j server before
driver = GraphDatabase.driver(uri, auth=("neo4j", "1234"))

######################### Example queries in Neo4j for analysis ###################
# The queries are in Cypher programming language

with driver.session() as session:
    
    # Overlapping topics. See which ones are subtopics of other topics.
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
    # Take 100 best nodes (nodes with more co-occurrences) and show the relations between them
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
    # All the relationships up to second degree from one InferedTool node 
    # Minimum citation first degree is 0, limited to 100 nodes
    # Minimum citations second degree is 50
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
            where k2.label="Omics" or k.label="Omics"
            with distinct n
            with collect(n) as nt
            unwind nt as nt1
            unwind nt as nt2
            match (nt1)-[m:METAOCCUR_ALL]-(nt2)
            return nt1,m,nt2
        """)
    # Query to retrieve relationships between communities with topics and size >1
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
    # Query to retrieve relationships between communities with languages and size >1
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
    # Query to retrieve relationships between communities with OS and size >1
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
    # Main topics of each graph
    session.run("""
        CALL {
            match (t:Keyword)<-[:TOPIC]-(n)
            with  collect(t) as topic, count(t) as ct
            return topic, ct
        }
        with ct, topic
        unwind topic as untop
        with untop, count(untop) as num, ct
        order by num DESC
        with untop, max(num) as number_of_times, ct as totalTopics
        where number_of_times >1
        return untop,toFloat(number_of_times)/totalTopics as percentage, number_of_times, totalTopics
        order by percentage desc, number_of_times desc
        """)
    # Jaccard index between most similar communities All vs. Methods
    session.run("""
        match (n1)-[:HAS_COMMUNITY]->(c1:Community)
        where c1.from_section="All"
        with c1.com_id as com1, collect(id(n1)) as cid1
        where size(cid1)>5
        match (n2)-[:HAS_COMMUNITY]->(c2:Community)
        where c2.from_section="METHODS"
        with com1, cid1,c2.com_id as com2, collect(id(n2)) as cid2
        where size(cid2)>5
        RETURN com1 AS from,
            com2 AS to,
            gds.alpha.similarity.jaccard(cid1, cid2) AS similarity
        order by similarity desc
        """)
