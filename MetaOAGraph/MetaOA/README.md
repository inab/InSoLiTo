## Merged Metadata and OpenAccess database of one use case
 
### To create a database for a merged Metadata and OpenAccess database of one Use Case in Neo4j you need to do the following:

1. From the Metadata relational database copy all your files in the import folder of your Neo4j project.

2. From the OpenAccess database, copy into the import folder of the Neo4j project the following files: the MetaCitations file for each section, the InferredTools table, and the InferedTools_to_Publications table.

3. Open your project in Neo4j.
 
4. Import the Publication nodes:

```
python3 neo4j_Publications.py
```

5. Import the InferedTools tables and keywords nodes and relationships:

```
python3 neo4j_infertools_key.py
```

6. Import the Metacitation table:

```
python3 neo4j_metacitations.py
```

7. Apply clustering and the centrality algorithm with the Graph Data Science library:

```
python3 data_science.py
```

Sometimes, if there are a huge amount of edges, you need to increase the `dbms.memory.heap.max_size` size.
