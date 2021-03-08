## Neo4j Files

- CreateDatabase folder, creates the database in Neo4j.

- data_science.py: Adds Page Rank and Louvain clustering to the properties of the nodes

- EDAM_biotools.py: Script that search in bio.tools the name of tools infered from the publications and the keywords of given the given tools.

- neo4j_simplify_tools_pub.py: Script that collapse all the publications from a tool. Currently, it doesn't work due to a bug in the "apoc" function from Neo4j.

- neo4j_simply_publications.py: Script that search in a file of OpenEBench the name of the tools of a given publication.

- possible_queries.py: Queries that can be done in the database
