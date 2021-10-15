#!/bin/bash

# Execution example:
# bash CreateMetaGraph.sh ../../database/Provaproteomics2 ../../PubEnricher/pruebaSAguiloAPE_2/ provaNeo4j csvfiles/

START="$(date +%s)"

echo "Starting bash"

db=$1
PubEnricherfolder=$2
Neo4jdatabasename=$3
outputfolder=$4 # Must be created before executing

# echo "Creating SQL database with name: $db"
# 
# python3 CreateSQLDatabase/CreateSQLDataset.py $db $PubEnricherfolder &&
#  
# sqlite3 $db.db "VACUUM;"
 
echo "Extracting csv file from database"
 
./convert-db-to-csv.sh $db.db $outputfolder &&

echo "Creating Neo4j database in docker with name: $Neo4jdatabasename"

docker run --name $Neo4jdatabasename -p7474:7474 -p7687:7687 -d -v $PWD/$outputfolder:/var/lib/neo4j/import --env NEO4J_AUTH=none -e NEO4J_apoc_export_file_enabled=true -e NEO4J_apoc_import_file_enabled=true -e NEO4J_apoc_import_file_use__neo4j__config=true -e NEO4JLABS_PLUGINS='["apoc", "graph-data-science"]' neo4j:4.2.3 

sleep 30;

echo "Creating nodes in the Neo4j database"

python3 CreateNeo4jDatabase/CreateNeo4jDataset.py;
# 
# DURATION=$[ $(date +%s) - ${START} ]
# echo "Whole execution lasts ${DURATION} seconds"
