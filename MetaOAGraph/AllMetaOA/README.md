# Create the merged Metadata and OpenAccess database from all the uses cases of the project

This implementation creates a graph database from the references of the research papers from the Publications domain.

- [CreateSQLDatabase](CreateSQLDatabase): Create the relational database with SQLite.
- [CreateNeo4jDatabase](CreateNeo4jDatabase): Create the graph database with Neo4j.

You must create the relational database before inserting the data into Neo4j.
