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

3. Infer tools from the publications. Create: the Inferedtools table for the infered tools; InferedTools-key table for the keywords of each tool; InferedTools_to_Publications table for the publications that infer a tool; and Metacitations, that create the edges between and within all the tools and edges:

```
python3 simply_infertools.py
```

