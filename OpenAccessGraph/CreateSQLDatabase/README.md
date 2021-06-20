## Creating the SQL OpenAccess database

Once you have all the Publications domain from `PubEnricher.py`, you can create the SQL database.

In each file you must put the name of the database where you want to store the data.

1. First, create the tables where the most of the data will be stored.

```
python3 create_tables.py
```

2. Then, create the publication nodes in the Publications table. You must write the path of your publications domain.

```
python3 simply_publications.py
```

3. Query all the citations from the EuropeanPMC website.

```
python3 query_citations.py
```

4. Then, calculate the sum of co-occurrences between the citations and insert in the backup tables.

```
python3 simply_citations.py
```

5. Infer tools and EDAM keywords from the publications.

```
python3 simply_infertools_key.py
```

6. Retrieve the relationships between the classes and subclasses.

```
python3 simply_add_EDAM_ontology.py
```
