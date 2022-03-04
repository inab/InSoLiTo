#!/bin/bash


echo "Starting script"

source .pyDBenv/bin/activate

Neo4jdatabasename=$1
outputfolder=$2 # Must be created before executing

echo "Creating Neo4j database in docker with name: $Neo4jdatabasename"

sudo docker run --name $Neo4jdatabasename -p7687:7687 -d -v $PWD/$outputfolder:/var/lib/neo4j/import --env NEO4J_AUTH=none -e NEO4J_apoc_export_file_enabled=true -e NEO4J_apoc_import_file_enabled=true -e NEO4J_apoc_import_file_use__neo4j__config=true -e NEO4JLABS_PLUGINS='["apoc", "graph-data-science"]'  -e NEO4J_dbms_memory_heap_max__size=6G -e NEO4J_dbms_memory_pagecache_size=6G neo4j:4.4.3 

sleep 45;

echo "Creating nodes in the Neo4j database"

python3 Neo4jScripts/CreateNeo4jDataset.py;
# 
# DURATION=$[ $(date +%s) - ${START} ]
# echo "Whole execution lasts ${DURATION} seconds"
