#!/bin/bash

echo "Starting bash"

db="path/to/InSoLiToSQLiteDB"
PubEnricherfolder="path/to/the/folder"
outputfolder="path/to/the/folder" # Must be created before executing

echo "Creating SQL database with name: $db"

python3 CreateSQLDatabase/CreateSQLDataset.py $db $PubEnricherfolder &&
 
sqlite3 $db.db "VACUUM;"
 
echo "Extracting csv file from database"
 
./convert-db-to-csv.sh $db.db $outputfolder
