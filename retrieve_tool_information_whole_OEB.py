import json
import urllib.request as request

# Download Publications json
url = "https://openebench.bsc.es/monitor/rest/search?=publications"
response = request.urlopen(url)
data = json.loads(response.read())


#with open("publications_060721.json") as json_file:
#data = json.load(json_file)
dict_pubs= {}
for tool in data:
    if "publications" not in tool:
        continue
    if len(tool["publications"]) ==0:
        continue
    if tool["name"] not in dict_pubs:
        dict_pubs[tool["name"]] = {}
        for pubs in tool["publications"]:
            for id_type, identifier in pubs.items():
                dict_pubs[tool["name"]][identifier] = id_type
    else:
        for pubs in tool["publications"]:
            for id_type, identifier in pubs.items():
                dict_pubs[tool["name"]][identifier] = id_type

output_file = open("openEBenchInfo.json", "w")
list_publications = []
for dict_tool,dict_id in dict_pubs.items():
    l_pubs = []
    for id_pub, type_pub in dict_id.items():
        out_pub = """
            {"%s" : "%s"}
        """ % (type_pub, id_pub)
        l_pubs.append(out_pub)
    
    out_text = """
        {
            "@id": "%s",
            "@type": "cmd",
            "@license": "https://creativecommons.org/licenses/by/4.0/",
            "@timestamp": "2019-01-24T11:15:00Z",
            "publications": [
                %s
            ]
        }
    """ % (dict_tool, ",".join(l_pubs))
    list_publications.append(out_text)
print(len(list_publications))
output_file.write(f"[{','.join(list_publications)}]")
