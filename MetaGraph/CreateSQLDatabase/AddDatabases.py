# Import libraries
import sqlite3
import time
import requests
import json

# Start time - Just to count how much the script lasts
start_time = time.time()

# Name of the database
DB_FILE = "database/MetaMolecular.db"

# Connect to the SQLite database
# If name not found, it will create a new database
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

def create_database_nodes():
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
    conn.commit()

            


if __name__ == '__main__':
    # Import ontology
    create_database_nodes()
    c.close()
    print("--- %s seconds ---" % (time.time() - start_time))

