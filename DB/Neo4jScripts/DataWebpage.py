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
        tools_graph = session.run("""
                match (n:Tool), (d:Database)
                with collect(n) as cn, collect(d) as cd
                with cn+cd as tools_nodes
                unwind tools_nodes as tools
                return distinct tools.name as name, id(tools) as id, labels(tools) as label
            """)
        
        topics_graph = session.run("""
            match ()-[e:METAOCCUR_ALL]-(n)-[:TOPIC]->(k:Keyword)-[:SUBCLASS*]->(k2:Keyword)
            where e.times>10
            with collect(distinct id(n)) as cn, collect(distinct id(e)) as ce,k
            return cn,ce,k.label as name
        """)
        tools = [{"value":tool["name"], "idNodes":tool["id"], "idEdges":[], "labelnode":tool["label"]} for tool in tools_graph]
        topics = [{"value":topic["name"], "idNodes":topic["cn"], "idEdges":topic["ce"], "labelnode":"Topic"} for topic in topics_graph]
        
        topics_and_tools = topics + tools

        count_relationships = session.run("""
            match ()-[m:METAOCCUR_ALL]->()
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
            
        
    with open("../sliderData.json","w") as outfile:
        json.dump(relations_log, outfile)
    with open("../ToolTopicAutocomplete.json","w") as outfile:
        json.dump(topics_and_tools, outfile)
