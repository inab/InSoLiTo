# Co-citation corpus: Europe PMC full-text download

`download_europepmc.py` downloads Open Access JATS full-text XML from the
[Europe PMC REST API](https://europepmc.org/RestfulWebService) for one or more topics.
By default it downloads proteomics and metabolomics.

```bash
pip install -r requirements.txt

# Smoke test: 50 articles per topic
python download_europepmc.py --limit 50 --contact you@example.org

# Full run (resumable: re-run the same command after an interruption)
python download_europepmc.py --topics proteomics metabolomics --contact you@example.org
```

Query per topic (override with `--query-template`):
`({topic}) AND OPEN_ACCESS:Y AND HAS_REFLIST:Y`

## Output (`data/`, git-ignored)

| Path | Contents |
|---|---|
| `search/<topic>.jsonl` | One search hit per line: pmcid, pmid, doi, title, journal, year, pubType |
| `xml/PMCxxx/PMCxxxxxxx.xml.gz` | Gzipped JATS full text, 10k files per folder |
| `manifest.tsv` | One row per unique article: IDs, topics it matched, pub type, download status |

`status` in the manifest is `ok`, `not_available` (Europe PMC returned 404) or `error: ...`.
Re-running retries everything that isn't `ok` unless you pass `--errors skip`.
Stopping a run with Ctrl+C or `kill` saves the manifest first.

## Options

- `--step search|fetch|all`: run only one step. `fetch` reuses the existing search results.
- `--errors retry|skip|only`: what to do with papers that failed in an earlier run (listed in `data/errors.tsv`).
  `skip` leaves them for later, and `only` retries just those.
- `--workers` (default 6) and `--max-rps` (default 8): parallel downloads, and a global cap on requests per second.
  Keep these modest. For the full 7.3M corpus, use the bulk FTP/S3 dumps instead of this API.

## Parsing: `parse_jats.py`

This turns the downloaded XML into three Parquet tables in `data/parsed/`. Each table is
written in shards of 2,000 papers, and shards already written are skipped on a re-run.

```bash
python parse_jats.py --workers 8          # about 25 min for 266k papers
pytest test_parse_jats.py                  # tests on hand-written XML
```

| Table | One row per | Key columns |
|---|---|---|
| `articles` | paper | `pmcid`, `article_type`, `n_refs`, `n_refs_cited`, `n_mentions`, `status` |
| `references` | reference-list entry | `pmcid`, `ref_id`, `ref_pos`, `pmid`, `pmcid_ref`, `doi`, `title`, `year`, `cited_rank`, `cited_rank_text` |
| `mentions` | in-text citation | `pmcid`, `mention_idx`, `ref_id`, `via`, `sec_class`, `sec_title`, `block_idx`, `sentence_idx`, `in_table`, `in_caption` |

How the parser works:

- **Citation order** comes from `<xref ref-type="bibr">` tags in reading order, so it is
  correct for numbered, author-year and hybrid styles. `cited_rank` is the order in which a
  reference is first cited. `cited_rank_text` ignores tables and figure captions, which JATS
  often places out of reading order.
- **Ranges** such as `[1–4]` are expanded to the references in between (`via = range`).
  So are ranges written inside a single citation tag (`text-range`) and tags that list
  several references (`multi-rid`).
- **`sec_class`** is the top-level section: `intro`, `methods`, `results`,
  `results_discussion`, `discussion`, `conclusion`, `back` (acknowledgements, funding, etc.),
  `other` (e.g. topic sections in reviews) or `none` (no sections).
- **Distance:** `block_idx` is the paragraph or table cell and `sentence_idx` is the
  sentence, both counted across the whole paper. Two references with the same
  `sentence_idx` were cited in the same sentence.
- **IDs:** DOIs are lower-cased and the `https://doi.org/` prefix is removed. DOIs are also
  picked up from links and from the citation text when there is no `<pub-id>`.

### Column reference

All three tables share `pmcid`, the citing paper. `references` and `mentions` join on
`(pmcid, ref_id)`.

**`articles`**: one row per citing paper

| Column | Meaning |
|---|---|
| `pmcid` | Citing paper (from the file name) |
| `article_type` | JATS `article-type`: `research-article`, `review-article`, `editorial`, ... |
| `n_refs` | Entries in the reference list |
| `n_refs_cited` | References cited at least once in the body |
| `n_mentions` | In-text citations, including those added by range expansion |
| `n_unresolved_mentions` | Citations whose `rid` matches no reference (should be about 0) |
| `n_sections` | Top-level `<sec>` count |
| `status` | `ok`, `no_body`, or `error: ...` |

**`references`**: one row per reference-list entry

| Column | Meaning |
|---|---|
| `ref_id` | The reference's XML id (`B12`, `CR5`, ...). Unique only within a paper |
| `ref_pos` | 1-based position in the reference list |
| `label` | Printed label (`"12"`, `"12."`), if any |
| `pmid`, `pmcid_ref`, `doi` | Cited paper's IDs. The DOI is lower-cased with no `https://doi.org/`. Taken from `<pub-id>`, then typed `<ext-link>`, then Europe PMC's Google Scholar link, then the citation text |
| `title`, `source`, `year`, `first_author` | Cited paper's title, journal, year and first author's surname |
| `publication_type` | `journal`, `book`, `web`, ... (when the XML gives it) |
| `citation_text` | Raw citation string, kept **only** when there is no PMID or DOI (for fuzzy matching) |
| `cited_rank` | Order of first citation in the body (1 = cited first). Empty if never cited |
| `cited_rank_text` | Same, but ignoring tables and figure captions. **Use this as the citation order** |
| `first_mention_idx` | `mention_idx` of the first citation |

**`mentions`**: one row per in-text citation, in reading order

| Column | Meaning |
|---|---|
| `mention_idx` | 0-based reading-order index within the paper |
| `ref_id`, `ref_pos` | Which reference is cited (join to `references`) |
| `via` | `xref` (explicit tag), `multi-rid` (one tag citing several), `range` (between the ends of "1–4"), `text-range` ("7-8" inside one tag) |
| `sec_class` | Top-level section: `intro`, `methods`, `results`, `results_discussion`, `discussion`, `conclusion`, `back`, `other`, `none` |
| `sec_title` | Title of the innermost section, e.g. `"2.3 Statistical analysis"` |
| `sec_idx` | Index of the top-level section (0-based) |
| `block_idx` | Paragraph or table cell, counted across the paper. Same value = same paragraph |
| `block_type` | `p`, `td`, `th`, `title`, ... |
| `sentence_idx` | Sentence, counted across the paper. Same value = same sentence |
| `char_offset` | Character position in the paper's body text |
| `in_table`, `in_caption` | Citation is inside a table or a figure/table caption |

## Sharing: `export_compact.py`

This packs `data/parsed/` into four single Parquet files in `data/export/`, plus a
`README.txt`, for sending to collaborators. Each cited paper is stored once in `works`, and
the slim `citations` table points to it by `work_id`. That roughly halves the size.

```bash
python export_compact.py        # a few minutes; uses DuckDB, so it can spill to disk
```

## TLS errors behind a corporate proxy

`CERTIFICATE_VERIFY_FAILED: self-signed certificate in certificate chain` means a
TLS-inspecting proxy sits between you and EBI. With `truststore` installed (it's in
`requirements.txt`, Python 3.10+) the script uses your OS certificate store, which
already trusts the proxy. Alternatively, pass `--ca-bundle /path/to/corp-root.pem`.
Don't disable verification.
