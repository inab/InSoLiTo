# InSoLiTo database

* Before starting to install the datase and its webpage, `docker` and `docker compose v2` is needed for the installation.

### Download the data

* If you want to use the data available from InSoLiTo, download the following data from [Zenodo](https://doi.org/10.5281/zenodo.6359386):

```
cd DB
wget https://zenodo.org/api/files/e8f78917-1d81-4fbd-a183-6605f33d14e3/InSoLiToImport.tar.gz 
tar -xzf InSoLiToImport.tar.gz
cd ..
```
* If you use your own data, create a folder in `DB/InSoLiToImport` and insert it there.

### Use Docker to compile the database with the webpage

* Then, in this directory use the following command line in detached mode:

```
docker compose up -d
```

The database, that will be empty, will be available in http://localhost:7474/browser/

### Populate the database

* Before populate the database, please follow the instructions in [DB/INSTALL.md](DB/INSTALL.md).

* Then, we need to insert all the CSV that we have download into the Neo4j database. Also, two files from the autocomplete and the slider part of the webpage will be created.
```
cd DB/
source .pyDBenv/bin/activate
python Neo4jScripts/CreateNeo4jDataset.py
python retrieve_json.py
deactivate
cd ..
```
### Compile the Webpage

Before starting, assure that the newest version of npm is installed:

```bash
mkdir REST/
mkdir REST/static
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

* Now, you have to run `webpack` in order to prepare and deploy the InSoLiTo site, which will be deployed at `../REST/static` subdirectory.

```bash
webpack --progress --color
cd ..
```

### Update the Docker webpage

* To update the webpage we need to stop the Webpage container:

```
docker stop insolito_webpack-ApacheServer-1
```

* And commit the new changes from the `REST/static` directory:

```
docker commit insolito_webpack-ApacheServer-1
```

Congratulations! The webpage will be available in http://localhost:0080/index-test.html