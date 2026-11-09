"""Pull every tool from bio.tools and extract its publication identifiers.

Step 1 (fetch):   page through https://bio.tools/api/tool/ and save every tool
                  record, unmodified, to data/biotools_raw.jsonl (one tool per line).
Step 2 (extract): read the raw file and write data/biotools_publications.csv, one row per
                  (tool, publication): biotoolsID, pmid, pmcid, doi, type, is_primary
                  Then pick each tool's main publication(s): those typed "Primary", or the first listed
                  publication if none is. bio.tools only annotates a publication type for some tools,
                  so is_primary is "false" on these fallback rows.
                  DOIs are lowercased (they are case-insensitive) with any trailing "." removed;
                  PMCIDs are uppercased.
Step 3 (split):   split the main publications by whether another tool has the same main publication:
                  - data/biotools_main_publications_unique.csv  main publications that belong to that
                                                                one tool only:
                                                                pmid, pmcid, doi, type, is_primary, biotoolsID
                  - data/biotools_main_publications_shared.csv  one row per paper that is the main
                                                                publication of several tools:
                                                                pmid, pmcid, doi, n_tools, biotoolsIDs (";"-joined)
                  The unique file keeps bio.tools' order; the shared file is sorted by n_tools,
                  largest first.
                  In the shared file, an identifier with several values ("|"-joined) means bio.tools
                  records disagree.
                  Rows are matched on any shared identifier, so a tool citing only the DOI and another
                  citing only the PMID of the same paper end up in the same group.

Usage:
    python3 pull_biotools.py                 # fetch, then extract
    python3 pull_biotools.py --extract-only  # re-run extraction on the saved raw file
    python3 pull_biotools.py --delay 0.5     # be gentler with the API (seconds between pages)
    python3 pull_biotools.py --extract-only --raw-file data/biotools_raw_14-10-2026.jsonl

Only the standard library is needed.
"""
import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://bio.tools/api/tool/?format=json&page={page}"
DATA_DIR = Path(__file__).resolve().parent / "data"
RAW_FILE = DATA_DIR / "biotools_raw.jsonl"
IDS_FILE = DATA_DIR / "biotools_publications.csv"
UNIQUE_FILE = DATA_DIR / "biotools_main_publications_unique.csv"
SHARED_FILE = DATA_DIR / "biotools_main_publications_shared.csv"
CSV_HEADER = ["biotoolsID", "pmid", "pmcid", "doi", "type", "is_primary"]

MAX_RETRIES = 5
TIMEOUT = 60  # seconds per request
DOI_PREFIXES = ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/", "doi:")


def get_page(page):
    """Return the decoded JSON for one API page, retrying transient failures."""
    request = urllib.request.Request(
        API_URL.format(page=page), headers={"User-Agent": "InSoLiTo-biotools-pull"}
    )
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            if attempt == MAX_RETRIES:
                raise RuntimeError(f"Page {page} failed after {MAX_RETRIES} attempts: {error}")
            wait = 2 ** attempt
            print(f"  page {page}: {error} - retrying in {wait}s", file=sys.stderr)
            time.sleep(wait)


def fetch_all(delay, raw_file):
    """Download all tools into raw_file. Written to a temp file first so a failed run never clobbers a good one."""
    DATA_DIR.mkdir(exist_ok=True)
    partial = raw_file.with_suffix(".jsonl.part")
    page, total, written = 1, None, 0
    with open(partial, "w", encoding="utf-8") as out:
        while True:
            data = get_page(page)
            if total is None:
                total = data["count"]
                print(f"bio.tools reports {total} tools")
            for tool in data["list"]:
                out.write(json.dumps(tool, ensure_ascii=False) + "\n")
            written += len(data["list"])
            print(f"  page {page}: {written}/{total}", end="\r", flush=True)
            if not data.get("next"):
                break
            page += 1
            time.sleep(delay)
    print()
    if written != total:
        # bio.tools can change while we page through it, so this is a warning, not an error
        print(f"Warning: expected {total} tools but received {written}", file=sys.stderr)
    partial.replace(raw_file)
    print(f"Saved {written} tools to {raw_file}")


def clean(value):
    """Strip whitespace; return '' for missing values."""
    return str(value).strip() if value else ""


def clean_doi(value):
    doi = clean(value)
    for prefix in DOI_PREFIXES:
        if doi.lower().startswith(prefix):
            doi = doi[len(prefix):]
            break
    # DOIs are case-insensitive; a trailing "." is citation punctuation, not part of the DOI
    return doi.rstrip(".").lower()


def clean_pmcid(value):
    return clean(value).upper()


def extract_ids(raw_file):
    """Write one CSV row per publication that has at least one of PMID/PMCID/DOI.

    `type` holds bio.tools' publication types joined with ";" (e.g. "Primary;Method"), empty if
    unannotated. A publication listed twice for one tool has its types merged into one row.
    """
    publications = {}  # (biotoolsID, pmid, pmcid, doi) -> list of types
    tools = 0
    with open(raw_file, encoding="utf-8") as raw:
        for line in raw:
            tool = json.loads(line)
            tools += 1
            for publication in tool.get("publication") or []:
                key = (
                    tool["biotoolsID"],
                    clean(publication.get("pmid")),
                    clean_pmcid(publication.get("pmcid")),
                    clean_doi(publication.get("doi")),
                )
                if not any(key[1:]):
                    continue
                types = publications.setdefault(key, [])
                types.extend(t for t in publication.get("type") or [] if t not in types)

    rows = [key + (";".join(types), str("Primary" in types).lower()) for key, types in publications.items()]

    # Main publication(s) per tool: those typed Primary, else the first one (rows keep bio.tools' order)
    rows_by_tool = {}
    for row in rows:
        rows_by_tool.setdefault(row[0], []).append(row)
    main_rows = []
    for tool_rows in rows_by_tool.values():
        primary = [row for row in tool_rows if row[-1] == "true"]
        main_rows.extend(primary or tool_rows[:1])

    with open(IDS_FILE, "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(CSV_HEADER)
        writer.writerows(rows)

    print(f"Read {tools} tools; {len({row[0] for row in rows})} have at least one publication ID")
    print(f"Saved {len(rows)} publication rows to {IDS_FILE}")
    fallback = sum(row[-1] == "false" for row in main_rows)
    print(f"Picked {len(main_rows)} main publications ({len(main_rows) - fallback} primary, "
          f"{fallback} first-listed fallback)")
    return main_rows


def split_shared(main_rows):
    """Group main publication rows by paper; write single-tool rows and multi-tool papers to separate files.

    Two rows are the same paper if they share a PMID, PMCID or DOI (union-find over identifiers).
    """
    parent = {}

    def find(node):
        parent.setdefault(node, node)
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for _, pmid, pmcid, doi, *_ in main_rows:
        ids = [(kind, value) for kind, value in (("pmid", pmid), ("pmcid", pmcid), ("doi", doi)) if value]
        for other in ids[1:]:
            parent[find(other)] = find(ids[0])

    groups = {}  # root -> {"rows": list, "tools": set, "pmid": set, "pmcid": set, "doi": set}
    for row in main_rows:
        tool, pmid, pmcid, doi = row[:4]
        root = find(next((kind, value) for kind, value in (("pmid", pmid), ("pmcid", pmcid), ("doi", doi)) if value))
        group = groups.setdefault(root, {"rows": [], "tools": set(), "pmid": set(), "pmcid": set(), "doi": set()})
        group["rows"].append(row)
        group["tools"].add(tool)
        for kind, value in (("pmid", pmid), ("pmcid", pmcid), ("doi", doi)):
            if value:
                group[kind].add(value)

    # Rows of single-tool papers, in bio.tools' order
    unique_rows = [row for row in main_rows if len(groups[find(next(
        (kind, value) for kind, value in zip(("pmid", "pmcid", "doi"), row[1:4]) if value))]["tools"]) == 1]
    with open(UNIQUE_FILE, "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        # Tool ID last, matching the shared file
        writer.writerow(CSV_HEADER[1:] + CSV_HEADER[:1])
        writer.writerows(row[1:] + row[:1] for row in unique_rows)
    print(f"Saved {len(unique_rows)} main publication rows used by a single tool to {UNIQUE_FILE}")

    shared = sorted([group for group in groups.values() if len(group["tools"]) > 1], key=lambda g: len(g["tools"]), reverse=True)
    with open(SHARED_FILE, "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(["pmid", "pmcid", "doi", "n_tools", "biotoolsIDs"])
        for group in shared:
            # Several values for one identifier mean bio.tools records disagree; keep them all, "|"-joined
            # (not ";", which occurs inside SICI-style DOIs)
            tools = list(dict.fromkeys(row[0] for row in group["rows"]))  # bio.tools' order
            writer.writerow(["|".join(sorted(group[k])) for k in ("pmid", "pmcid", "doi")]
                            + [len(tools), ";".join(tools)])

    tools = sum(len(group["tools"]) for group in shared)
    print(f"Saved {len(shared)} papers shared by {tools} tools to {SHARED_FILE}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--extract-only", action="store_true", help="skip the download and reuse the saved raw file")
    parser.add_argument("--raw-file", type=Path, default=RAW_FILE,
                        help=f"raw bio.tools dump to write/read (default: {RAW_FILE.relative_to(DATA_DIR.parent)})")
    parser.add_argument("--delay", type=float, default=0.2, help="seconds to wait between pages (default: 0.2)")
    args = parser.parse_args()

    if not args.extract_only:
        fetch_all(args.delay, args.raw_file)
    elif not args.raw_file.exists():
        sys.exit(f"{args.raw_file} not found - run without --extract-only first")
    split_shared(extract_ids(args.raw_file))


if __name__ == "__main__":
    main()
