# InSoLiTo database

Before starting to install the datase and its webpage, `docker` and `docker compose v2` are needed for the installation.

If you wanto to create the database from zero, you need to follow the steps from the `DB` folder.

Otherwise, the data used for creating the graph of InSoLiTo can be downloaded from Zenodo or use the one available at the [InSoLiTo webpage](https://insolito.openebench.bsc.es/).

### Create the database

* If you want to use the data available from InSoLiTo, download the following data from [Zenodo](https://doi.org/10.5281/zenodo.7524268):

```
cd DB
wget https://zenodo.org/api/files/fc67bc5a-14b9-47d5-8e4f-29eca185609a/InSoLiToImport.zip
unzip InSoLiToImport.zip
cd ..
```
* If you use your own data, create a folder called `InSoLiToImport` inside `DB` and insert your CSV files there. Make sure that it has the same structure as the files in `InSoLiToImport.tar.gz`.

In case you want to use the data avaiblable at the InSoLiTo Webpage, you need to download the following support files from [Zenodo](https://doi.org/10.5281/zenodo.13740843):

```
cd DB
wget https://zenodo.org/api/files/a56be092-6407-4a12-baca-92099d8da511/InSoLiToSupportFiles.zip
unzip InSoLiToSupportFiles.zip
mv InSoLiToSupportFiles/* .   
cd ..
```

### Use Docker to compile the database with the webpage

From here, either you have download the data from Zenodo or it has been created from scratch, you can continue the installation of project.

* Before starting, we create the folders where the webpage will be outputted:

```
mkdir -p REST/static
```

* Then, in the root directory use the following command line:

```
docker compose up -d
```

The docker containers will be running in detached mode. You can check the logs with `docker compose logs`.

The Neo4j database, that is empty at the moment, is available in http://localhost:7474/browser/. The database might not be ready until 1 minute after running the `docker compose` command.

### Populate the database

If you are making API request to the database created at [InSoLiTo webpage](https://insolito.openebench.bsc.es/), you can avoid this step.

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

The current installation is done with `npm` v8.19.4 and `node` v16.20.2.

* Install `webpack` and `webpack-li` with npm:

```
cd FRONTEND
npm install webpack webpack-cli --save-dev
```

* Now, you have to run `webpack` in order to prepare and deploy the InSoLiTo site, which will be deployed at `../REST/static` subdirectory. Before running the command, make sure that the database credentials in the `FRONTEND/src/config.json` file are correct to connect the webpage with the database.

```bash
npm run build
```

Congratulations! The webpage will be available at [REST/static/index.html](REST/static/index.html)


## Adding the InSoLiTo API

In case you want to add the [InSoLiTo API](https://github.com/inab/InSoLiToAPI) to the webpage, you need to do the following.

```
cd InSoLiTo #root folder of the repository
git clone https://github.com/inab/InSoLiToAPI
docker compose -f docker-compose.apache-node.yml up --build --force-recreate
```

If you have completed the README correctly, you should have the webpage available at [http://localhost:3000/home/](http://localhost:3000/home/). The other endpoints and how to search them can be found in the README of the [InSoLiTo API](https://github.com/inab/InSoLiToAPI) repository.