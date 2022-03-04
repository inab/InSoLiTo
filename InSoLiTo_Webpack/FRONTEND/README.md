# Install instructions of InSoLiTo
  
*Installation

```bash
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
webpack --progress --colors
```

* Congratulations! InSoLiTo browser is available at the `../REST/static` subdirectory.
