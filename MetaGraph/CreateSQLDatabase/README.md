## Creating the SQL Metadata database

Once you have all the publications from `PubEnricher.py`, you can create the SQL database.

In each file you must put the name of the database where you want to store the data.

1. First, create the tables where the most of the data will be stored.

```
python3 create_tables.py
```

2. Then, create the publication nodes in the Publications table. You must write the path of your publications domain.

```
python3 simply_publications.py
```

3. Then, create the publication-publication edges in table "Citations":

```
python3 simply_citations.py
```

4. Infer tools and EDAM keywords from the publications.

```
python3 simply_infertools_key.py
```

5. Add subclasses in the EDAM ontology terms.

```
python3 simply_add_EDAM_ontology.py
```

6. Difference Tools and Databases

```
python3 AddDatabases.py
```
