# Install libraries for creating the database

For storing the information in the database, Python 3.5 or later is needed. The script used depends on standard libreries, plus the ones declared in [requirements.txt](requirements.txt).

* In order to install the dependencies you need `pip` and `venv` Python modules.
	- `pip` is available in many Linux distributions (Ubuntu package `python-pip`, CentOS EPEL package `python-pip`), and also as [pip](https://pip.pypa.io/en/stable/) Python package.
	- `venv` is also available in many Linux distributions (Ubuntu package `python3-venv`). In some of these distributions `venv` is integrated into the Python 3.5 (or later) installation.

* The creation of a virtual environment and installation of the dependencies in that environment is done running:

```bash
python3 -m venv .pyDBenv
source .pyDBenv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt -c constraints.txt
deactivate
```
Moreover, you need `docker` installed in your computer.