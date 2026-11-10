"""
Download Galaxy workflows and their metadata from WorkflowHub. Everything goes to data/download/.

Step 1 (list):     every workflow ID on WorkflowHub          -> index.json
Step 2 (metadata): one JSON per workflow, unmodified         -> meta/<id>.json
Step 3 (crates):   RO-Crate zip of each Galaxy workflow       -> crates/<id>_v<version>.crate.zip
                   and the .ga file(s) inside it              -> ga/<id>_v<version>/<name>.ga
Step 4 (summary):  one row per workflow (all types)           -> workflows.csv
                   id, version, title, workflow_class, topics, operations, tools, ga_files

Wen running with --limit, the summary goes to workflows_limit.csv instead, so a test run does not replace the full table.

No topic filter is applied here: most workflows have no topic annotations, so filtering
at download time would drop them. Topics are saved in workflows.csv to filter later.

Runs can be stopped and restarted: files already on disk are not downloaded again.
Reading public workflows needs no account or token.

Usage (from the repository root):
    .venv/bin/python directed-graph/workflowhub/download_workflowhub.py --limit 5   # test on 5 workflows
    .venv/bin/python directed-graph/workflowhub/download_workflowhub.py             # everything
    .venv/bin/python directed-graph/workflowhub/download_workflowhub.py --summary-only
"""
import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

BASE = "https://workflowhub.org"
DATA_DIR = Path(__file__).resolve().parent / "data" / "download"
INDEX_FILE = DATA_DIR / "index.json"
META_DIR = DATA_DIR / "meta"
CRATE_DIR = DATA_DIR / "crates"
GA_DIR = DATA_DIR / "ga"
SUMMARY_FILE = DATA_DIR / "workflows.csv"

USER_AGENT = "BH2026-InSoLiTo workflowhub harvester (python urllib)"
MAX_RETRIES = 5
TIMEOUT = 60  # seconds per request

# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #

def fetch(url, accept="application/json"):
    """GET a URL and return the body as bytes. Retries with increasing waits."""
    request = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": USER_AGENT})
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code in (403, 404):  # private or deleted: retrying will not help
                raise
            reason = f"HTTP {error.code}"
        except (urllib.error.URLError, TimeoutError) as error:
            reason = str(error)
        wait = 2 ** attempt
        print(f"  retry {attempt}/{MAX_RETRIES} in {wait}s ({reason}): {url}", file=sys.stderr)
        time.sleep(wait)
    raise RuntimeError(f"Gave up after {MAX_RETRIES} attempts: {url}")


def fetch_json(url):
    return json.loads(fetch(url))


# --------------------------------------------------------------------------- #
# Step 1: list all workflow IDs
# --------------------------------------------------------------------------- #

def list_workflows():
    """Return all workflow IDs, following pagination links if the API uses them."""
    ids = []
    url = f"{BASE}/workflows"
    while url:
        page = fetch_json(url)
        ids.extend(item["id"] for item in page.get("data", []))
        next_link = (page.get("links") or {}).get("next")
        url = (BASE + next_link if next_link and next_link.startswith("/") else next_link) or None
    ids = sorted(set(ids), key=int)
    INDEX_FILE.write_text(json.dumps(ids))
    print(f"Found {len(ids)} workflows")
    return ids


# --------------------------------------------------------------------------- #
# Step 2: metadata per workflow
# --------------------------------------------------------------------------- #

def get_metadata(workflow_id, delay):
    """Return the workflow's JSON, downloading it only if not saved yet."""
    path = META_DIR / f"{workflow_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    time.sleep(delay)
    try:
        metadata = fetch_json(f"{BASE}/workflows/{workflow_id}")
    except (urllib.error.HTTPError, RuntimeError) as error:
        print(f"  skip {workflow_id}: {error}", file=sys.stderr)
        return None
    path.write_text(json.dumps(metadata, indent=1))
    return metadata


def attributes(metadata):
    return (metadata or {}).get("data", {}).get("attributes", {})


def workflow_class(attrs):
    """'Galaxy', 'Nextflow', ... The API may give a dict or a plain string."""
    value = attrs.get("workflow_class")
    if isinstance(value, dict):
        return value.get("title") or value.get("key") or ""
    return value or ""


def latest_version(attrs):
    if attrs.get("latest_version"):
        return attrs["latest_version"]
    versions = [v.get("version") for v in attrs.get("versions") or [] if v.get("version")]
    return max(versions) if versions else 1


def labels(items):
    """Turn a list of annotation dicts (or strings) into 'a;b;c'."""
    out = []
    for item in items or []:
        if isinstance(item, dict):
            out.append(str(item.get("label") or item.get("name") or item.get("title") or item.get("id") or ""))
        else:
            out.append(str(item))
    return ";".join(x for x in out if x)


# --------------------------------------------------------------------------- #
# Step 3: RO-Crate and .ga files of Galaxy workflows
# --------------------------------------------------------------------------- #

def get_crate(workflow_id, version, delay):
    """Download the RO-Crate zip if not saved yet. Returns its path or None."""
    path = CRATE_DIR / f"{workflow_id}_v{version}.crate.zip"
    if path.exists():
        return path
    time.sleep(delay)
    try:
        body = fetch(f"{BASE}/workflows/{workflow_id}/ro_crate?version={version}", accept="application/zip")
    except (urllib.error.HTTPError, RuntimeError) as error:
        print(f"  no crate for {workflow_id} v{version}: {error}", file=sys.stderr)
        return None
    path.write_bytes(body)
    return path


def extract_ga(crate_path, workflow_id, version):
    """Copy every .ga file in the crate to ga/<id>_v<version>/. Returns their names."""
    out_dir = GA_DIR / f"{workflow_id}_v{version}"
    try:
        with zipfile.ZipFile(crate_path) as crate:
            names = [n for n in crate.namelist() if n.endswith(".ga")]
            out_dir.mkdir(parents=True, exist_ok=True)
            for name in names:
                (out_dir / Path(name).name).write_bytes(crate.read(name))
    except zipfile.BadZipFile:
        print(f"  not a zip: {crate_path}", file=sys.stderr)
        return []
    return [Path(n).name for n in names]


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, help="only the first N workflows (for testing)")
    parser.add_argument("--delay", type=float, default=0.5, help="seconds between requests (default: 0.5)")
    parser.add_argument("--summary-only", action="store_true", help="rebuild workflows.csv from saved files")
    args = parser.parse_args()

    for folder in (DATA_DIR, META_DIR, CRATE_DIR, GA_DIR):
        folder.mkdir(parents=True, exist_ok=True)

    ids = json.loads(INDEX_FILE.read_text()) if args.summary_only else list_workflows()
    if args.limit:
        ids = ids[:args.limit]

    rows = []
    for n, workflow_id in enumerate(ids, 1):
        metadata = get_metadata(workflow_id, 0 if args.summary_only else args.delay)
        attrs = attributes(metadata)
        if not attrs:
            continue
        version = latest_version(attrs)
        wf_class = workflow_class(attrs)
        ga_files = []
        if wf_class.lower() == "galaxy" and not args.summary_only:
            crate = get_crate(workflow_id, version, args.delay)
            if crate:
                ga_files = extract_ga(crate, workflow_id, version)
        elif wf_class.lower() == "galaxy":
            ga_dir = GA_DIR / f"{workflow_id}_v{version}"
            ga_files = sorted(p.name for p in ga_dir.glob("*.ga")) if ga_dir.exists() else []

        rows.append({
            "id": workflow_id,
            "version": version,
            "title": attrs.get("title", ""),
            "workflow_class": wf_class,
            "topics": labels(attrs.get("topic_annotations")),
            "operations": labels(attrs.get("operation_annotations")),
            "tools": labels(attrs.get("tools")),
            "ga_files": ";".join(ga_files),
        })
        if n % 50 == 0:
            print(f"  {n}/{len(ids)}")

    summary_file = SUMMARY_FILE.with_name("workflows_limit.csv") if args.limit else SUMMARY_FILE
    if summary_file.exists():
        print(f"Note: overwriting {summary_file.name}") # TODO: make it a formal warning/error?
    with open(summary_file, "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]) if rows else ["id"])
        writer.writeheader()
        writer.writerows(rows)

    galaxy = [r for r in rows if r["workflow_class"].lower() == "galaxy"]
    print(f"Wrote {summary_file.name}: {len(rows)} workflows, {len(galaxy)} Galaxy, "
          f"{sum(1 for r in galaxy if r['ga_files'])} with a .ga file")


if __name__ == "__main__":
    main()
