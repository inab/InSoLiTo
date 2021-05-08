## Creating the SQL database

Once you have all the publications from `PubEnricher.py`, you can create the SQL database.

1. First, create the publication nodes in table "Publications":

```
python3 simply_publications.py
```

2. Then, create the tables where the citations will be stored.

```
python3 create_tables.py
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
