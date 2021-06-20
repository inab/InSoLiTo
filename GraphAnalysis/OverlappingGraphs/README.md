# Calculating overlap between the graphs

The Python script query the relationships of a graph and, the R script creates calculate the overlap of relationships between the sections or use cases.

For querying with the Python script, you first need to open your Neo4j database of interest.

For the OpenAccess database you need to open a graph with the Metadata and OpenAccess database together.

- Run [OverlapOpenAccess.py](OverlapOpenAccess.py) Python 3 script.

```
python3 OverlapOpenAccess.py <OutputFile> <MinCoocurrences>

Argument    <OutputFile>: Location of the Output file.
Argument    <MinCoocurrences>: Mininum number of co-occurrences between the nodes.

```

For the Metadata database you need to open the Metadata database in Neo4j for each use case you want to use. And to compare the results you need to run the script with the graph having all the use cases.

- Run [OverlapMetadata.py](OverlapMetadata.py) Python 3 script.

```
python3 OverlapMetadata.py <OutputFile> <MinCoocurrences>

Argument    <OutputFile>: Location of the Output file.
Argument    <MinCoocurrences>: Mininum number of co-occurrences between the nodes.

```

After you have the files, you can open and run the R script.
