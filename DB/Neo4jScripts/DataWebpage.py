import json
import math

def logslider(position, minv, maxv):
    #position between 0 and 100
    minp = 0
    maxp = 100
    
    # Results between 11 and Max occurrences in database
    minv= math.log(minv)
    maxv= math.log(maxv)
    
    # Scale the values
    scale = (maxv-minv) / (maxp-minp)
    
    value = math.trunc(math.exp(minv + scale*(position-minp)))
    
    return value


def CreateToolsTopicsList(driver):
    with driver.session() as session:
        
        # Tool and topic information
        tools_graph = session.run("""
                match (n:Tool), (d:Database)
                with collect(n) as cn, collect(d) as cd
                with cn+cd as tools_nodes
                unwind tools_nodes as tools
                return distinct tools.name as name, id(tools) as id, labels(tools) as label, tools.toolType as type
            """)
        
        topics_graph = session.run("""
            match ()-[e:METAOCCUR_ALL]-(n)-[:TOPIC]->(k:Keyword)-[:SUBCLASS*]->(k2:Keyword)
            where e.times>10
            with collect(distinct id(n)) as cn, collect(distinct id(e)) as ce,k
            return cn,ce,k.label as name
        """)
        tools = [{"value":tool["name"], "idNodes":tool["id"], "labelnode":tool["label"], "type":tool["type"]} for tool in tools_graph]
        topics = [{"value":topic["name"], "idNodes":topic["cn"], "labelnode":"Topic", "type":[]} for topic in topics_graph]
        topics_and_tools = topics + tools
        
        communityInformation = session.run("""
            match (n)-[q:HAS_COMMUNITY]->(p)
            with p, count(q) as cq
            return cq, p.mtopic,p.mlanguage, p.mos, p.com_id
            order by cq DESC
            """)
        communityData = [{"id":community["p.com_id"], "Topic":community["p.mtopic"], "Language":community["p.mlanguage"], "OS":community["p.mos"], "totalNodes":community["cq"]} for community in communityInformation]
        
        # Relationships slider information
        count_relationships = session.run("""
            match (q)-[m:METAOCCUR_ALL]-()
            where EXISTS(q.name)
            return m.times as times, count(m.times) as ctimes
            order by m.times
            """)
        minv = 1000000
        maxv = 0
        relations_all = {}
        for relationships in count_relationships:
            if relationships["times"]< minv:
                minv = relationships["times"]
            if relationships["times"]> maxv:
                maxv = relationships["times"]
            relations_all[relationships["times"]]=math.log(relationships["ctimes"])

        relations_log = {}
        for i in range(101):
            value = logslider(i, minv,maxv)
            if value in relations_all:
                relations_log[value]=relations_all[value]
            else:
                res = relations_all.get(value) or min(relations_all.keys(), key = lambda key: abs(key-value))
                relations_log[res] = relations_all[res]
        
        # Year slider information
        count_year = session.run("""
            match (q)-[m:METAOCCUR]->()
            where exists(q.name)
            return m.year as years, count(m.year) as cyear
            order by m.year
            """)
        year_slider_info = {}
        for year in count_year:
            year_slider_info[year["years"]] = year["cyear"]
        
    with open("../RelationshipSliderData.json","w") as outfile:
        json.dump(relations_log, outfile)
    with open("../YearSliderData.json","w") as outfile:
        json.dump(year_slider_info, outfile)
    with open("../ToolTopicAutocomplete.json","w") as outfile:
        json.dump(topics_and_tools, outfile)
    with open("../CommunityData.json","w") as outfile:
        json.dump(communityData, outfile)
