"""Count OpenEBench tools that have at least one publication with a PMID or DOI.

Reads the snapshot downloaded from
https://openebench.bsc.es/monitor/rest/search?=publications
into DB/raw_data/oeb_tools.json.

Mirrors the filter in DB/pipeline/InferToolsKeywords.py (lines 168-188),
minus the check that the publication exists in the PubMed dump, so the result
is an upper bound for the number of tools a rebuilt InSoLiTo would contain.
"""

import json
from collections import Counter
from pathlib import Path

OEB_FILE = Path(__file__).resolve().parent.parent / "raw_data" / "oeb_tools.json"


def has_pmid_or_doi(entry):
    return any("pmid" in pub or "doi" in pub for pub in entry["publications"])


def main():
    with open(OEB_FILE) as f:
        entries = json.load(f)

    with_publications = [e for e in entries if e.get("publications")]
    with_ids = [e for e in with_publications if has_pmid_or_doi(e)]
    # OEB returns one entry per tool variant (web, cmd, lib...); the pipeline
    # keeps one tool per bio.tools label
    labels = {e.get("@label") for e in with_ids}

    print("Total entries:", len(entries))
    print("With publications:", len(with_publications))
    print("With PMID or DOI:", len(with_ids))
    print("Distinct labels with PMID or DOI:", len(labels))

    # Breakdown by source registry (@nmsp) and deprecation, counting distinct
    # labels within each group
    print("\nDistinct labels with PMID or DOI, by source:")
    by_source = {}
    for e in with_ids:
        by_source.setdefault(e.get("@nmsp"), set()).add(e.get("@label"))
    for source, source_labels in sorted(by_source.items(), key=lambda x: -len(x[1])):
        print(f"  {source}: {len(source_labels)}")

    deprecated = Counter(bool(e.get("deprecated")) for e in with_ids)
    print("\nEntries with PMID or DOI, deprecated:", deprecated[True])
    print("Entries with PMID or DOI, not deprecated:", deprecated[False])
    active_labels = {e.get("@label") for e in with_ids if not e.get("deprecated")}
    print("Distinct labels with PMID or DOI, not deprecated:", len(active_labels))


if __name__ == "__main__":
    main()
