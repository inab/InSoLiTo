"""Pull every tool from bio.tools and extract its publication identifiers.

Step 1 (fetch):   page through https://bio.tools/api/tool/ and save every tool
                  record, unmodified, to data/biotools_raw.jsonl (one tool per line).
Step 2 (extract): read the raw file and write two CSVs with one row per (tool, publication):
                  biotoolsID, pmid, pmcid, doi, type, is_primary
                  - data/biotools_publications.csv       every publication
                  - data/biotools_main_publications.csv  per tool: its "Primary" publication(s), or the
                                                         first listed publication if none is Primary
                  bio.tools only annotates a publication type for some tools, so is_primary is "false"
                  on the fallback rows of the second file.

Usage:
    python3 pull_biotools.py                 # fetch, then extract
    python3 pull_biotools.py --extract-only  # re-run extraction on the saved raw file
    python3 pull_biotools.py --delay 0.5     # be gentler with the API (seconds between pages)

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
MAIN_FILE = DATA_DIR / "biotools_main_publications.csv"
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


def fetch_all(delay):
    """Download all tools into RAW_FILE. Written to a temp file first so a failed run never clobbers a good one."""
    DATA_DIR.mkdir(exist_ok=True)
    partial = RAW_FILE.with_suffix(".jsonl.part")
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
    partial.replace(RAW_FILE)
    print(f"Saved {written} tools to {RAW_FILE}")


def clean(value):
    """Strip whitespace; return '' for missing values."""
    return str(value).strip() if value else ""


def clean_doi(value):
    doi = clean(value)
    for prefix in DOI_PREFIXES:
        if doi.lower().startswith(prefix):
            doi = doi[len(prefix):]
            break
    return doi


def extract_ids():
    """Write one CSV row per publication that has at least one of PMID/PMCID/DOI.

    `type` holds bio.tools' publication types joined with ";" (e.g. "Primary;Method"), empty if
    unannotated. A publication listed twice for one tool has its types merged into one row.
    """
    publications = {}  # (biotoolsID, pmid, pmcid, doi) -> list of types
    tools = 0
    with open(RAW_FILE, encoding="utf-8") as raw:
        for line in raw:
            tool = json.loads(line)
            tools += 1
            for publication in tool.get("publication") or []:
                key = (
                    tool["biotoolsID"],
                    clean(publication.get("pmid")),
                    clean(publication.get("pmcid")),
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

    for path, selected in ((IDS_FILE, rows), (MAIN_FILE, main_rows)):
        with open(path, "w", newline="", encoding="utf-8") as out:
            writer = csv.writer(out)
            writer.writerow(CSV_HEADER)
            writer.writerows(selected)

    print(f"Read {tools} tools; {len({row[0] for row in rows})} have at least one publication ID")
    print(f"Saved {len(rows)} publication rows to {IDS_FILE}")
    fallback = sum(row[-1] == "false" for row in main_rows)
    print(f"Saved {len(main_rows)} main publication rows ({len(main_rows) - fallback} primary, "
          f"{fallback} first-listed fallback) to {MAIN_FILE}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--extract-only", action="store_true", help="skip the download and reuse the saved raw file")
    parser.add_argument("--delay", type=float, default=0.2, help="seconds to wait between pages (default: 0.2)")
    args = parser.parse_args()

    if not args.extract_only:
        fetch_all(args.delay)
    elif not RAW_FILE.exists():
        sys.exit(f"{RAW_FILE} not found - run without --extract-only first")
    extract_ids()


if __name__ == "__main__":
    main()
