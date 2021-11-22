# Import libraries
import requests
import json


def create_database_nodes(c):
    c.execute(f"""
              SELECT label
              from InferedTools
              """)
    labels=c.fetchall()
    for label in labels:
        label = label[0]
        req = f'https://openebench.bsc.es/monitor/rest/search?id={label}'
        r = requests.get(req)
        json_file = r.json()
        for i in json_file:
            if i["@type"]=="db":
                c.execute(f"""UPDATE InferedTools SET node_type='Database' where label='{label}';""")

