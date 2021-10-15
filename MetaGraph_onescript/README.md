# Create the Metadata database

This implementation creates a graph database for the references of all the metadata of the research papers from the Publications domain.

- [CreateSQLDatabase](CreateSQLDatabase): Create the relational database with SQLite.

- [CreateNeo4jDatabase](CreateNeo4jDatabase): Create the graph database with Neo4j.

You must create the relational database before inserting the data into Neo4j.

If youn want to do this in one step, you must run the following bash script (You must need to have docker installed):

```

bash CreateMetaGraph.sh SQLiteDatabaseName PubEnricherFolder NameNeo4jDatabase TablesOutputFolder

```

After that you can see that with ``` docker ps ``` that you have the Neo4j database in your computer.
