# InSoLiTo database

Before starting to install the datase and its webpage, `docker` and `docker compose v2` is needed for the installation.

If you wanto to create the database from zero, you need to follow the steps from the `DB` folder.

Otherwise, the data used for creating the graph of InSoLiTo can be downloaded from Zenodo.

### Download the data

* If you want to use the data available from InSoLiTo, download the following data from [Zenodo](https://doi.org/10.5281/zenodo.7524268):

```
cd DB
wget https://zenodo.org/api/files/fc67bc5a-14b9-47d5-8e4f-29eca185609a/InSoLiToImport.zip
unzip InSoLiToImport.zip
cd ..
```
* If you use your own data, create a folder called `InSoLiToImport` inside `DB` and insert your CSV files there. Make sure that it has the same structure as the files in `InSoLiToImport.tar.gz`.

### Use Docker to compile the database with the webpage

From here, either you have download the data from Zenodo or it has been created from scratch, you can continue the installation of project.

* Before starting, we create the folders where the webpage will be outputted:

```
mkdir REST/
mkdir REST/static
```

* Then, in the root directory use the following command line:

```
docker compose up -d
```

The docker containers will be running in detached mode. You can check the logs with `docker compose logs`.

The Neo4j database, that is empty at the moment, is available in http://localhost:7474/browser/. The database might not be ready until 1 minute after running the `docker compose` command.

### Populate the database

* Before populate the database, if you do not have the Neo4j library for Python 3 please follow the instructions in [DB/Neo4jScripts/Install.md](DB/Neo4jScripts/Install.md).

* Then, we need to create the nodes and relationships into the Neo4j database. The name of each file can be modified in the `sample-config.ini` file. There, you can also modify the database credentials (url, user and password).

```
cd DB/Neo4jScripts/
source .pyDBenv/bin/activate    # Needed if you do not have Neo4j library in Python
python CreateNeo4jDataset.py sample-config.ini
deactivate
cd ../..
```

You can check the full graph database in http://localhost:7474/browser/.

Also, two files for running the autocomplete and the slider part of the webpage will be created.

### Compile the Webpage

* Assure that the newest version of npm is installed:

```
cd FRONTEND
npm install --no-save npm
```

* Add `node_modules/.bin` subdirectory to the `PATH` environment variable, so newest `npm`, `yarn` and other installation dependencies can be instantiated:

```
PATH="$(npm bin):${PATH}"
export PATH
```

* Next line installs [Yarn](https://yarnpkg.com/) installation dependency, which is used to fetch [Webpack](https://webpack.github.io/) and other dependencies:

```
npm install --no-save yarn
```

* Then, call `yarn`, so the other dependencies are fetched:

```bash
yarn --frozen-lockfile
```

* Now, you have to run `webpack` in order to prepare and deploy the InSoLiTo site, which will be deployed at `../REST/static` subdirectory. Before running the command, make sure that the database credentials in the `FRONTEND/app/config.json` file are correct to connect the webpage with the database.

```bash
webpack --progress --color
```

Congratulations! The webpage will be available at [REST/static/index.html](REST/static/index.html)
