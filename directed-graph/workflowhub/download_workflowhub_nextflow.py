"""
Download all Nextflow workflows and their metadata from WorkflowHub
(with --ignore-nfcore: except those in the space "nf-core").

Step 1 (list):     every workflow ID on WorkflowHub          -> data/download/index.json
                   with --ignore-nfcore: the nf-core space   -> data/download/nextflow_excluded_space_nf-core.json
Step 2 (metadata): one JSON per workflow, unmodified         -> data/download/meta/<id>.json
Step 3 (crates):   RO-Crate zip of each Nextflow workflow    -> data/download/crates/<id>_v<version>.crate.zip
                   unpacked (the whole pipeline)             -> data/download/nextflow/<id>_v<version>/
                   incomplete crates (only a link to a git repository, empty or HTML .nf files, missing
                   included files) are filled from a shallow `git clone` of the repository
                   (needs git; the clone runs no code; --no-clone skips this)
Step 4 (summary):  one row per downloaded Nextflow workflow  -> data/download/nextflow/nextflow_workflows.csv
                   id, version, title, projects, topics, operations, tools, nf_files

Index, metadata and crates are shared with download_workflowhub.py, so neither script downloads them twice.
Runs can be stopped and restarted: files already on disk are not downloaded again.
Reading public workflows needs no account or token.

Usage (from the repository root):
    python3 directed-graph/workflowhub/download_workflowhub_nextflow.py --limit 10  # test on 10 workflows
    python3 directed-graph/workflowhub/download_workflowhub_nextflow.py             # everything
    python3 directed-graph/workflowhub/download_workflowhub_nextflow.py --summary-only
    python3 directed-graph/workflowhub/download_workflowhub_nextflow.py --ignore-nfcore  # without nf-core
"""
import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

from nfdag.build import build

BASE = "https://workflowhub.org"
DATA_DIR = Path(__file__).resolve().parent / "data" / "download"  # shared with download_workflowhub.py
INDEX_FILE = DATA_DIR / "index.json"
META_DIR = DATA_DIR / "meta"
CRATE_DIR = DATA_DIR / "crates"
NF_DIR = DATA_DIR / "nextflow"
SUMMARY_FILE = NF_DIR / "nextflow_workflows.csv"

EXCLUDED_SPACE = 4  # "nf-core" (WorkflowHub calls spaces "programmes" in the API)

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
# Step 1: list all workflow IDs, and the teams of the excluded space
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


def excluded_projects(offline):
    """Return the IDs of the teams (projects) in the excluded space."""
    path = DATA_DIR / "nextflow_excluded_space_nf-core.json"
    if offline and path.exists():
        programme = json.loads(path.read_text())
    else:
        programme = fetch_json(f"{BASE}/programmes/{EXCLUDED_SPACE}")
        path.write_text(json.dumps(programme, indent=1))
    data = programme.get("data", {})
    projects = {p["id"] for p in data.get("relationships", {}).get("projects", {}).get("data", [])}
    print(f"Excluding space '{data.get('attributes', {}).get('title')}': teams {sorted(projects, key=int)}")
    return projects


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


def project_ids(metadata):
    """IDs of the teams (projects) the workflow belongs to."""
    relationships = (metadata or {}).get("data", {}).get("relationships", {})
    return [p["id"] for p in (relationships.get("projects") or {}).get("data") or []]


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
# Step 3: RO-Crate of Nextflow workflows, unpacked
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


def nf_files(out_dir):
    """Paths of the .nf files below out_dir, relative to it."""
    return sorted(str(p.relative_to(out_dir)) for p in out_dir.rglob("*.nf")) if out_dir.exists() else []


def extract_crate(crate_path, workflow_id, version):
    """Unpack the whole crate to data/nextflow/<id>_v<version>/. Returns its .nf files."""
    out_dir = NF_DIR / f"{workflow_id}_v{version}"
    if out_dir.exists():
        return nf_files(out_dir)
    try:
        with zipfile.ZipFile(crate_path) as crate:
            out_dir.mkdir(parents=True)
            for member in crate.infolist():
                name = PurePosixPath(member.filename)
                if member.is_dir() or name.is_absolute() or ".." in name.parts:  # no writing outside out_dir
                    continue
                target = out_dir.joinpath(*name.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(crate.read(member))
    except zipfile.BadZipFile:
        print(f"  not a zip: {crate_path}", file=sys.stderr)
        return []
    return nf_files(out_dir)


def repository(out_dir, attrs, version):
    """(git URL, ref) the workflow version was registered from, from the crate or the metadata."""
    url = ""
    try:
        graph = json.loads((out_dir / "ro-crate-metadata.json").read_text())["@graph"]
        root = next(e for e in graph if e.get("@id") == "./")
        url = root.get("isBasedOn") or ""
        url = url.get("@id", "") if isinstance(url, dict) else url
    except (OSError, ValueError, KeyError, StopIteration):
        pass
    ref = ""
    for v in attrs.get("versions") or []:
        if v.get("version") == version:
            url = url or v.get("remote") or ""
            ref = v.get("ref") or ""
    url = url.split("/-/")[0].split("?")[0].rstrip("/")  # GitLab: .../repo/-/tree/main?ref_type=heads
    ref = ref.removeprefix("refs/heads/").removeprefix("refs/tags/").removeprefix("refs/remotes/origin/")
    return url, ref


def is_html(path):
    """A web page saved under a .nf name (some crates hold the GitLab page instead of the file)."""
    return path.read_text(errors="replace")[:500].lstrip().lower().startswith(("<!doctype html", "<html"))


def replaceable(path):
    """Whether a crate file may be overwritten from the clone: missing, empty, or a saved web page."""
    if not path.exists():
        return True
    return path.is_file() and (path.stat().st_size == 0 or (path.suffix == ".nf" and is_html(path)))


def incomplete(out_dir):
    """Why a crate is incomplete (no, empty or HTML .nf files, or an include its DAG needs is missing), or None."""
    nf = list(out_dir.rglob("*.nf"))
    if not nf or any(replaceable(p) for p in nf):
        return "no, empty or HTML .nf files"
    try:  # the DAG extractor: only includes on the way from the entry workflow count, not those of unused files
        missing = [w for w in build(out_dir).warnings if w.startswith("include not found")]
    except Exception:  # a crate the extractor cannot read is not a reason to clone
        return None
    return missing[0] if missing else None


def fill_from_repository(out_dir, attrs, version):
    """Some crates only link to a git repository, or miss files (git submodules, included modules): clone it and
    fill the gaps. Files from the crate win; only missing, empty or HTML files are taken from the clone.
    Each crate is tried once: .cloned_from records the result."""
    marker = out_dir / ".cloned_from"
    reason = None if marker.exists() else incomplete(out_dir)
    if reason is None:
        return
    url, ref = repository(out_dir, attrs, version)
    if not url.startswith("https://"):
        print(f"  {out_dir.name}: incomplete crate ({reason}) and no repository link", file=sys.stderr)
        marker.write_text("failed: no repository link\n")
        return
    with tempfile.TemporaryDirectory(dir=DATA_DIR) as tmp:
        clone = Path(tmp) / "repo"
        command = ["git", "-c", "protocol.file.allow=never", "clone", "--quiet", "--depth", "1",
                   "--recurse-submodules", "--shallow-submodules"]
        env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
        attempts = [[*command, "--branch", ref, url, str(clone)]] if ref else []
        attempts.append([*command, url, str(clone)])  # the default branch, if the ref is gone
        for attempt in attempts:
            shutil.rmtree(clone, ignore_errors=True)
            result = subprocess.run(attempt, env=env, capture_output=True, text=True, timeout=600, check=False)
            if result.returncode == 0:
                break
        else:
            print(f"  {out_dir.name}: git clone failed for {url}: {result.stderr.strip()[:200]}", file=sys.stderr)
            marker.write_text(f"failed: {url} {ref}\n")
            return
        for path in clone.rglob("*"):
            relative = path.relative_to(clone)
            if ".git" in relative.parts or path.is_symlink() or not path.is_file():
                continue
            target = out_dir / relative
            if replaceable(target):
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
    marker.write_text(f"{url} {ref}\n")
    print(f"  {out_dir.name}: filled from {url} ({ref or 'default branch'}), because of: {reason}")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, help="stop after N downloaded Nextflow workflows (for testing)")
    parser.add_argument("--delay", type=float, default=0.5, help="seconds between requests (default: 0.5)")
    parser.add_argument("--summary-only", action="store_true", help="rebuild nextflow_workflows.csv from saved files")
    parser.add_argument("--no-clone", action="store_true", help="do not clone repositories of incomplete crates")
    parser.add_argument("--ignore-nfcore", action="store_true", help="skip the workflows of the nf-core space")
    args = parser.parse_args()

    for folder in (DATA_DIR, META_DIR, CRATE_DIR, NF_DIR):
        folder.mkdir(parents=True, exist_ok=True)

    ids = json.loads(INDEX_FILE.read_text()) if args.summary_only else list_workflows()
    excluded = excluded_projects(offline=args.summary_only) if args.ignore_nfcore else set()

    rows = []
    nextflow_total = 0
    for n, workflow_id in enumerate(ids, 1):
        metadata = get_metadata(workflow_id, 0 if args.summary_only else args.delay)
        attrs = attributes(metadata)
        if n % 50 == 0:
            print(f"  {n}/{len(ids)}")
        if not attrs or workflow_class(attrs).lower() != "nextflow":
            continue
        nextflow_total += 1
        projects = project_ids(metadata)
        if excluded.intersection(projects):
            continue

        version = latest_version(attrs)
        if args.summary_only:
            files = nf_files(NF_DIR / f"{workflow_id}_v{version}")
        else:
            crate = get_crate(workflow_id, version, args.delay)
            files = extract_crate(crate, workflow_id, version) if crate else []
            if crate and not args.no_clone:
                fill_from_repository(NF_DIR / f"{workflow_id}_v{version}", attrs, version)
                files = nf_files(NF_DIR / f"{workflow_id}_v{version}")

        rows.append({
            "id": workflow_id,
            "version": version,
            "title": attrs.get("title", ""),
            "projects": ";".join(projects),
            "topics": labels(attrs.get("topic_annotations")),
            "operations": labels(attrs.get("operation_annotations")),
            "tools": labels(attrs.get("tools")),
            "nf_files": ";".join(files),
        })
        if args.limit and len(rows) >= args.limit:
            break

    with open(SUMMARY_FILE, "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]) if rows else ["id"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {SUMMARY_FILE}: {nextflow_total} Nextflow workflows, "
          f"{nextflow_total - len(rows)} skipped (nf-core space or --limit), {len(rows)} kept, "
          f"{sum(1 for r in rows if r['nf_files'])} with a .nf file")


if __name__ == "__main__":
    main()
