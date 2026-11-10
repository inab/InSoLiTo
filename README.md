# InSoLiTo

**InSoLiTo** (Interactions of Software for Life Sciences Tools) shows which research software tools are used together, based on how often their papers are cited together (co-citation). Live version: https://test-insolito.openebench.bsc.es/

This is the repository of **BioHackathon Europe 2026, Project 17**: [*Bridging Literature and Practice: Tool Co-citation Networks from Publications and Registered Workflows*](https://github.com/elixir-europe/biohackathon-projects-2026/blob/main/17.md). On top of co-citation, it adds **directed edges**: which tool is cited before which in the text of an article.

## Repository layout

```
frontend/              Web app (Nuxt 4, Vue 3, Cytoscape.js)
DB/                    InSoLiTo database
├── pipeline/          Scripts that build it: PubMed + tool catalogue → SQLite → CSV → Neo4j
├── raw_data/          Inputs and intermediate files (not in git)
├── CONF/ DATA/ LOGS/ PLUGINS/ InSoLiToImport/   Neo4j volumes
└── *.json             Static data bundled into the web app
directed-graph/        Directed edges from citation order
├── europepmc/         Download and parse the full-text corpus from Europe PMC
├── biotools/          Publications of each bio.tools tool
└── citation-order/    Build the directed edges (steps 01 → 05b)
deploy/                Apache config, and the web app config for a local Neo4j
docker-compose.yml     Web app build + Neo4j + Apache
requirements.txt       Python packages for DB/pipeline/ and directed-graph/citation-order/
```

## Run locally with Docker

You need Docker with Compose v2.

```bash
cp .env.example .env
mkdir -p DB/InSoLiToImport frontend/.output/public
docker compose up -d
```

- On Linux, set `HOST_UID` and `HOST_GID` in `.env` to your `id -u` and `id -g`, so the files the containers create belong to you.
- The first run builds the web app inside Docker (a few minutes). Then open http://localhost:8080 (`INSOLITO_PORT`). The Neo4j browser is at http://localhost:7474 (`NEO4J_HTTP_PORT`).
- By default the web app queries the **public InSoLiTo database**. To use your local Neo4j, set `INSOLITO_CONFIG=./deploy/neo4j-local.json` in `.env` and run `docker compose up -d --force-recreate`.

To work on the web app only, without Docker (Node ≥ 22.19):

```bash
cd frontend
npm install
npm run dev
```

## Populate the local Neo4j

Create the Python environment once, from the repository root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

> **The import deletes everything in the Neo4j database it points to.** Use it only against your local Neo4j. The connection is set in `DB/pipeline/neo4j/*.ini` (`url_neo4j_server`): its port must match `NEO4J_BOLT_PORT` in your `.env`.

### Option A: published data (fast)

The data behind the current InSoLiTo (2023) is on Zenodo: [10.5281/zenodo.7524268](https://doi.org/10.5281/zenodo.7524268). With Neo4j running (`docker compose up -d`), from the repository root:

```bash
wget -P DB https://zenodo.org/records/7524268/files/InSoLiToImport.zip
cd DB && unzip -o InSoLiToImport.zip && cd ..
.venv/bin/python DB/pipeline/neo4j/CreateNeo4jDataset.py DB/pipeline/neo4j/local-config.ini
```

To see it in the web app, set `INSOLITO_CONFIG=./deploy/neo4j-local.json` in `.env` and run `docker compose up -d --force-recreate`.

### Option B: rebuild from scratch (hours)

Put the inputs in `DB/raw_data/`:

- `pubmed_baseline/`: the PubMed baseline XML files (~54 GB), from https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/
- `oeb_tools.json`: the OpenEBench tool catalogue, from https://openebench.bsc.es/monitor/rest/search?=publications

Stop Neo4j (`docker compose down`) and run, from the repository root:

```bash
nohup DB/pipeline/run_pipeline.sh > DB/raw_data/pipeline.log 2>&1 &
```

It builds the SQLite database, exports the CSV files to `DB/InSoLiToImport/`, starts Neo4j, imports them and writes the web app JSON files to `DB/raw_data/json_full/` (copy them to `DB/` to use them in the web app). `REUSE_PUBLICATIONS=1` reuses the publications table of a previous run.

## Directed graph

Inputs:

- **Corpus**: the Parquet tables in `directed-graph/europepmc/data/export/`. To build them, see [`directed-graph/europepmc/README.md`](directed-graph/europepmc/README.md) (those scripts run from their own folder, with their own `requirements.txt`).
- **Tool publications**: `directed-graph/biotools/data/biotools_publications.csv` (in git; refresh it with `pull_biotools.py`).

Run each step from the repository root, in order (seconds to a few minutes each). Each one writes its result to `directed-graph/citation-order/data/`, and the next step reads it:

```bash
.venv/bin/python directed-graph/citation-order/01_match_tools.py
```

| Step | What it does |
|---|---|
| `01_match_tools.py` | Finds which bio.tools papers are cited in the corpus (by DOI, PMID or PMCID) |
| `01b_top_works.py` | Check: the most cited works and their tool, if any |
| `02_filter_articles.py` | Keeps research articles |
| `03_order_tools.py` | Position of each tool in each article (Methods section by default, `SECTION` at the top) |
| `04_directed_pairs.py` | One row per tool pair and article, with the earlier cited tool as source |
| `05_sum_pairs.py` | One row per pair and direction: number of articles, share and distance |
| `05b_cytoscape.py` | Filtered edge list for Cytoscape (thresholds at the top of the script) |

To read how two tools are cited together, `pair_contexts.py` takes two bio.tools IDs. It counts the articles that cite both, grouped by whether the two citations share a sentence or a paragraph, and by which tool comes first. It reads the delta and tool gap from the outputs of steps 3 to 5 in `directed-graph/edges-processed/` (`EDGES` at the top of the script). It writes `directed-graph/citation-order/data/pair_contexts/<tool_a>__<tool_b>.html`. The page shows the pair's two edges from `directed_edges.csv`, and histograms of both distances over the pair's articles. For 15 articles, split across the groups by their size, it downloads the full text from Europe PMC and shows where each tool falls among the references, and the paragraphs that cite either tool with each tool's citations highlighted in its own colour:

```bash
.venv/bin/python directed-graph/citation-order/pair_contexts.py star deseq2
```

## Data sources

- [PubMed baseline](https://pubmed.ncbi.nlm.nih.gov/download/) (NLM): reference lists, for co-citation
- [OpenEBench](https://openebench.bsc.es/): tool catalogue
- [EDAM ontology](https://edamontology.org/): topics and operations
- [Europe PMC](https://europepmc.org/): Open Access full text, for citation order
- [bio.tools](https://bio.tools/): tool publications

Supporting files of the current InSoLiTo: [10.5281/zenodo.13740843](https://doi.org/10.5281/zenodo.13740843).

## License

MIT. See [LICENSE.txt](LICENSE.txt).
