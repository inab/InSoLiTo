## Creating the SQL database

Once you have all the publications from `PubEnricher.py`, you can create the SQL database.

1. First, create the publication nodes running:

```
python3 simply_publications.py
```

2. Then, create the publication-publication edges:

```
python3 simply_citations.py
```

3. Create the tool table and tool-publication table:

```
python3 simply_tools.py
```

4. Infer tools from the publication. Create the Infertool table, InferTool-Publication table and InferTool-Citation:

```
python3 simply_infertools.py
```

