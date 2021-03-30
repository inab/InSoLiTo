## Creating the SQL database

Once you have all the publications from `PubEnricher.py`, you can create the SQL database.

1. First, create the publication nodes in table "Publications":

```
python3 simply_publications.py
```

2. Then, create the publication-publication edges in table "Citations":

```
python3 simply_citations.py
```

3. Infer tools and EDAM keywords from the publications.

```
python3 simply_infertools_key.py
```

