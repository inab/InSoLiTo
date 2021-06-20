# Create the OpenAccess database

This implementation creates a graph database for the references of the Open Access research papers from the Publications domain.

- [CreateSQLDatabase](CreateSQLDatabase): Create the relational database with SQLite.

- [CreateNeo4jDatabase](CreateNeo4jDatabase): Create the graph database with Neo4j.

You must create the relational database before inserting the data into Neo4j.
