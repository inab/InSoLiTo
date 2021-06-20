## Creating the SQL database

Once you have all the publications from `PubEnricher.py`, you can create the SQLite database.

In each file you must put the name of the database where you want to store the data.

1. First, create the publication nodes in table "Publications":

```
python3 simply_publications.py
```

2. Then, create the tables where the citations will be stored.

```
python3 create_tables.py
```

3. Then, calculate the sum of co-occurrences between the citations and insert in the backup tables.

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
