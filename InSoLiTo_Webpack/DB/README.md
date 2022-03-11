# InSoLiTo database

* Before creating the database, please follow the instructions in [INSTALL.md](INSTALL.md). Also, `docker` is needed for the installation.

* Then, in the `DB` directory use the following command line:

```bash
bash CreateMetaGraph.sh 
```

After a while the docker database will be created.

* The database file is called `InSoLiToDB`, and it is available via Docker.

* Create the files for the autocomplete and the slider of the webpage:

```
source .pyDBenv/bin/activate
python retrieve_json.py
deactivate
```

If the database is stopped, write the following to restart:

```bash
docker start InSoLiToDB
```