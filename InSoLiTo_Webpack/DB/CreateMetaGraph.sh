#!/bin/bash

echo "Starting script"

source .pyDBenv/bin/activate

echo "Creating Neo4j database in docker with name: InSoLiToDB"

docker run --name InSoLiToDB -p7687:7687 -d -v $PWD/data:/var/lib/neo4j/import --env NEO4J_AUTH=none -e NEO4J_apoc_export_file_enabled=true -e NEO4J_apoc_import_file_enabled=true -e NEO4J_apoc_import_file_use__neo4j__config=true -e NEO4JLABS_PLUGINS='["apoc", "graph-data-science"]'  -e NEO4J_dbms_memory_heap_max__size=6G -e NEO4J_dbms_memory_pagecache_size=6G neo4j:4.4.3 

sleep 45;

echo "Creating nodes in the Neo4j database"

python3 Neo4jScripts/CreateNeo4jDataset.py;