"""Download Open Access JATS full-text XML from Europe PMC for one or more topics.

Two steps, both resumable:

1. search  - page through the Europe PMC search API (cursorMark) for each topic and
             write article metadata (PMCID, PMID, DOI, pubType, year, journal) to
             ``<out>/search/<topic>.jsonl``.
2. fetch   - download ``/{PMCID}/fullTextXML`` for the de-duplicated union of all
             topics into ``<out>/xml/<shard>/<PMCID>.xml.gz``. Files already on disk
             are skipped, so an interrupted run can simply be restarted.

A combined ``<out>/manifest.tsv`` records which topics each article came from and
the download status (ok / not_available / error).

Example::

    python download_europepmc.py --topics proteomics metabolomics --workers 6
    python download_europepmc.py --topics proteomics --limit 50   # smoke test
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import fcntl
import logging
import os
import signal
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("europepmc")

# Use the OS certificate store (macOS Keychain / Windows cert store) instead of
# certifi's bundle when available. Needed behind TLS-inspecting corporate proxies
# (e.g. Zscaler), whose root CA is installed in the OS but not in certifi.
try:
    import truststore

    truststore.inject_into_ssl()
    _TRUSTSTORE = True
except ImportError:
    _TRUSTSTORE = False

BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"
# Mirrors the query in the project doc: OA papers with a reference list.
DEFAULT_QUERY_TEMPLATE = "({topic}) AND OPEN_ACCESS:Y AND HAS_REFLIST:Y"
SEARCH_PAGE_SIZE = 1000  # API maximum
METADATA_FIELDS = (
    "pmcid", "pmid", "doi", "title", "journalTitle", "pubYear", "pubType",
    "isOpenAccess", "citedByCount",
)


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #

_thread_local = threading.local()


def _build_session(user_agent: str) -> requests.Session:
    """Session with retries/backoff on transient errors (honours Retry-After)."""
    retry = Retry(
        total=6,
        backoff_factor=2,  # 0, 2, 4, 8, 16, 32 s
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry, pool_maxsize=4))
    session.headers["User-Agent"] = user_agent
    if _CA_BUNDLE:
        session.verify = _CA_BUNDLE
    return session


_CA_BUNDLE: str | None = None


def get_session(user_agent: str) -> requests.Session:
    """One session per thread (requests.Session is not guaranteed thread-safe)."""
    if not hasattr(_thread_local, "session"):
        _thread_local.session = _build_session(user_agent)
    return _thread_local.session


class RateLimiter:
    """Global minimum interval between requests across all threads."""

    def __init__(self, max_per_second: float) -> None:
        self._interval = 1.0 / max_per_second if max_per_second > 0 else 0.0
        self._lock = threading.Lock()
        self._next = 0.0

    def wait(self) -> None:
        if not self._interval:
            return
        with self._lock:
            now = time.monotonic()
            sleep_for = self._next - now
            self._next = max(now, self._next) + self._interval
        if sleep_for > 0:
            time.sleep(sleep_for)


# --------------------------------------------------------------------------- #
# Step 1: search
# --------------------------------------------------------------------------- #


def search_topic(
    topic: str,
    query_template: str,
    out_file: Path,
    user_agent: str,
    limiter: RateLimiter,
    max_records: int | None = None,
) -> int:
    """Harvest all hits for a topic into a JSONL file. Returns number of records.

    Written to a temp file and renamed at the end, so a partial file never
    masquerades as a complete one. Re-running overwrites (search is cheap).
    """
    query = query_template.format(topic=topic)
    session = get_session(user_agent)
    tmp_file = out_file.with_suffix(".jsonl.part")
    out_file.parent.mkdir(parents=True, exist_ok=True)

    cursor = "*"
    n_written = 0
    hit_count = None
    with tmp_file.open("w") as fh:
        while True:
            limiter.wait()
            resp = session.get(
                f"{BASE_URL}/search",
                params={
                    "query": query,
                    "resultType": "lite",
                    "format": "json",
                    "pageSize": SEARCH_PAGE_SIZE,
                    "cursorMark": cursor,
                },
                timeout=120,
            )
            resp.raise_for_status()
            payload = resp.json()
            if hit_count is None:
                hit_count = payload.get("hitCount", 0)
                logger.info("[%s] query=%r  hitCount=%s", topic, query, hit_count)

            results = payload.get("resultList", {}).get("result", [])
            for rec in results:
                if not rec.get("pmcid"):
                    continue  # full text XML is keyed on PMCID
                row = {k: rec.get(k) for k in METADATA_FIELDS}
                row["topic"] = topic
                fh.write(json.dumps(row) + "\n")
                n_written += 1
                if max_records and n_written >= max_records:
                    break

            next_cursor = payload.get("nextCursorMark")
            logger.info("[%s] %d / %s", topic, n_written, hit_count)
            if (
                not results
                or not next_cursor
                or next_cursor == cursor
                or (max_records and n_written >= max_records)
            ):
                break
            cursor = next_cursor

    tmp_file.replace(out_file)
    logger.info("[%s] wrote %d records with PMCID -> %s", topic, n_written, out_file)
    return n_written


# --------------------------------------------------------------------------- #
# Step 2: fetch
# --------------------------------------------------------------------------- #


@dataclass
class Article:
    pmcid: str
    pmid: str | None = None
    doi: str | None = None
    pub_type: str | None = None
    pub_year: str | None = None
    journal: str | None = None
    topics: set[str] = field(default_factory=set)


def load_articles(search_dir: Path, topics: list[str]) -> dict[str, Article]:
    """Merge per-topic search results into one de-duplicated PMCID -> Article map."""
    articles: dict[str, Article] = {}
    for topic in topics:
        path = search_dir / f"{safe_name(topic)}.jsonl"
        if not path.exists():
            raise FileNotFoundError(f"No search results for {topic!r}: {path}. Run the search step first.")
        with path.open() as fh:
            for line in fh:
                rec = json.loads(line)
                art = articles.get(rec["pmcid"])
                if art is None:
                    art = articles[rec["pmcid"]] = Article(
                        pmcid=rec["pmcid"],
                        pmid=rec.get("pmid"),
                        doi=rec.get("doi"),
                        pub_type=rec.get("pubType"),
                        pub_year=rec.get("pubYear"),
                        journal=rec.get("journalTitle"),
                    )
                art.topics.add(topic)
    return articles


def xml_path(xml_dir: Path, pmcid: str) -> Path:
    """Shard into folders of <=10k files: PMC1234567 -> xml/PMC123/PMC1234567.xml.gz."""
    return xml_dir / pmcid[:-4] / f"{pmcid}.xml.gz"


def fetch_one(pmcid: str, dest: Path, user_agent: str, limiter: RateLimiter) -> str:
    """Download one article. Returns 'ok', 'skipped', 'not_available' or 'error: ...'."""
    if dest.exists() and dest.stat().st_size > 0:
        return "skipped"
    session = get_session(user_agent)
    limiter.wait()
    try:
        resp = session.get(f"{BASE_URL}/{pmcid}/fullTextXML", timeout=120)
    except requests.RequestException as exc:
        return f"error: {type(exc).__name__}"
    if resp.status_code == 404:
        return "not_available"
    if resp.status_code != 200:
        return f"error: HTTP {resp.status_code}"
    body = resp.content
    # Cheap sanity check: must look like a JATS article, not an HTML error page.
    if b"<article" not in body[:5000]:
        return "error: not JATS"

    dest.parent.mkdir(parents=True, exist_ok=True)
    # Unique temp name per writer, then an atomic rename: a crash never leaves a
    # truncated .xml.gz, and concurrent writers can't trip over each other's temp file.
    fd, tmp_name = tempfile.mkstemp(dir=dest.parent, prefix=f".{pmcid}.", suffix=".part")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb") as fh:
            fh.write(body)
        tmp.replace(dest)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return "ok"


def acquire_run_lock(out_dir: Path):
    """Hold an exclusive lock on <out>/.download.lock for the life of the process.

    Prevents two runs writing into the same output folder. The OS releases the lock
    automatically if the process dies, so there is no stale-lock cleanup to do.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    lock_path = out_dir / ".download.lock"
    fh = lock_path.open("a+")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fh.seek(0)
        other = fh.read().strip() or "unknown"
        raise SystemExit(
            f"Another download is already running on {out_dir} (PID {other}). "
            f"Stop it first (kill {other}) or wait for it to finish."
        )
    fh.seek(0)
    fh.truncate()
    fh.write(str(os.getpid()))
    fh.flush()
    return fh  # keep a reference so the lock is held


def fetch_all(
    articles: dict[str, Article],
    xml_dir: Path,
    manifest_file: Path,
    user_agent: str,
    limiter: RateLimiter,
    workers: int,
    limit: int | None,
    errors: str = "retry",
) -> None:
    # Carry forward failures recorded by earlier runs, so they survive in the
    # manifest even when this run doesn't (re)try them.
    previous = load_previous_failures(manifest_file)
    failed = {p for p in previous if p in articles}

    if errors == "only":
        todo = sorted(failed)
    elif errors == "skip":
        todo = sorted(set(articles) - failed)
    else:
        todo = sorted(articles)
    if limit:
        todo = todo[:limit]
    logger.info("Fetching full text for %d articles with %d workers (errors=%s, %d known failures)",
                len(todo), workers, errors, len(failed))

    status: dict[str, str] = {p: previous[p] for p in failed}
    counts: dict[str, int] = {}
    # Wall-clock time: time.monotonic() pauses while a Mac sleeps, which makes rates misleading.
    t0 = time.time()
    pool = ThreadPoolExecutor(max_workers=workers)
    try:
        futures = {
            pool.submit(fetch_one, pmcid, xml_path(xml_dir, pmcid), user_agent, limiter): pmcid
            for pmcid in todo
        }
        for i, fut in enumerate(as_completed(futures), 1):
            pmcid = futures[fut]
            result = fut.result()
            status[pmcid] = result
            key = result.split(":")[0]
            counts[key] = counts.get(key, 0) + 1
            if key == "error":
                logger.warning("%s %s", pmcid, result)
            if i % 500 == 0 or i == len(todo):
                rate = i / max(time.time() - t0, 1e-6)
                eta_min = (len(todo) - i) / rate / 60 if rate else 0
                logger.info("%d/%d  %s  (%.1f/s, ETA %.0f min)", i, len(todo), counts, rate, eta_min)
            if i % 5000 == 0:
                write_manifest(articles, status, xml_dir, manifest_file)  # checkpoint
    except KeyboardInterrupt:
        logger.warning("Interrupted - saving manifest before exiting.")
        raise
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
        write_manifest(articles, status, xml_dir, manifest_file)
    logger.info("Done: %s. Manifest -> %s", counts, manifest_file)
    if counts.get("error"):
        logger.info("Retry failures later with --errors only (successful files are always skipped).")


def is_failure(status: str) -> bool:
    return status.startswith("error") or status == "not_available"


def load_previous_failures(manifest_file: Path) -> dict[str, str]:
    """PMCID -> status for every error / not_available row in an existing manifest."""
    if not manifest_file.exists():
        return {}
    with manifest_file.open(newline="") as fh:
        return {
            row["pmcid"]: row["status"]
            for row in csv.DictReader(fh, delimiter="\t")
            if is_failure(row.get("status", ""))
        }


def write_manifest(
    articles: dict[str, Article], status: dict[str, str], xml_dir: Path, manifest_file: Path
) -> None:
    """One row per article across all topics, with current on-disk status.

    Also writes errors.tsv next to it: just the failed PMCIDs and why.
    """
    tmp = manifest_file.with_suffix(".tsv.part")
    failures: list[tuple[str, str]] = []
    with tmp.open("w", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(["pmcid", "pmid", "doi", "topics", "pub_type", "pub_year", "journal", "status", "xml_path"])
        for pmcid in sorted(articles):
            art = articles[pmcid]
            path = xml_path(xml_dir, pmcid)
            st = status.get(pmcid) or ("ok" if path.exists() else "pending")
            if st == "skipped" or path.exists():
                st = "ok"  # a file on disk wins over any older error
            elif is_failure(st):
                failures.append((pmcid, st))
            writer.writerow([
                art.pmcid, art.pmid or "", art.doi or "", ",".join(sorted(art.topics)),
                art.pub_type or "", art.pub_year or "", art.journal or "", st,
                str(path.relative_to(xml_dir.parent)) if st == "ok" else "",
            ])
    tmp.replace(manifest_file)

    errors_file = manifest_file.with_name("errors.tsv")
    tmp = errors_file.with_suffix(".tsv.part")
    with tmp.open("w", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(["pmcid", "status"])
        writer.writerows(failures)
    tmp.replace(errors_file)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def safe_name(topic: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in topic.lower()).strip("_")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--topics", nargs="+", default=["proteomics", "metabolomics"],
                   help="Search terms, one per topic (default: proteomics metabolomics).")
    p.add_argument("--query-template", default=DEFAULT_QUERY_TEMPLATE,
                   help="Europe PMC query; '{topic}' is substituted (default: %(default)s).")
    p.add_argument("--out", type=Path, default=Path(__file__).parent / "data",
                   help="Output directory (default: DB/CoCitation/data).")
    p.add_argument("--step", choices=["search", "fetch", "all"], default="all")
    p.add_argument("--workers", type=int, default=6, help="Parallel downloads (default: 6).")
    p.add_argument("--max-rps", type=float, default=8.0,
                   help="Global cap on requests per second (default: 8). Be polite.")
    p.add_argument("--limit", type=int, default=None,
                   help="Only search/fetch this many articles per run (for smoke tests).")
    p.add_argument("--contact", default="",
                   help="Contact email added to the User-Agent so EBI can reach you if needed.")
    p.add_argument("--ca-bundle", default=None,
                   help="Path to a PEM CA bundle (e.g. your corporate root CA) to verify TLS against.")
    p.add_argument("--errors", choices=["retry", "skip", "only"], default="retry",
                   help="Papers that failed in an earlier run (per manifest.tsv): retry them along with "
                        "everything else (default), skip them, or retry only them.")
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args(argv)


def _raise_keyboard_interrupt(signum, frame):  # noqa: ARG001
    raise KeyboardInterrupt


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    # Treat `kill <pid>` (SIGTERM) like Ctrl+C, so the manifest is still saved.
    signal.signal(signal.SIGTERM, _raise_keyboard_interrupt)

    global _CA_BUNDLE
    _CA_BUNDLE = args.ca_bundle
    logger.debug("TLS: truststore=%s ca_bundle=%s", _TRUSTSTORE, _CA_BUNDLE)
    user_agent = "BH2026-InSoLiTo co-citation harvester"
    if args.contact:
        user_agent += f" (mailto:{args.contact})"

    search_dir = args.out / "search"
    xml_dir = args.out / "xml"
    limiter = RateLimiter(args.max_rps)
    _lock = acquire_run_lock(args.out)  # noqa: F841 - held until exit

    if args.step in ("search", "all"):
        for topic in args.topics:
            search_topic(topic, args.query_template, search_dir / f"{safe_name(topic)}.jsonl",
                         user_agent, limiter, max_records=args.limit)

    if args.step in ("fetch", "all"):
        articles = load_articles(search_dir, args.topics)
        overlap = sum(1 for a in articles.values() if len(a.topics) > 1)
        logger.info("%d unique articles across %d topics (%d in more than one topic)",
                    len(articles), len(args.topics), overlap)
        fetch_all(articles, xml_dir, args.out / "manifest.tsv", user_agent, limiter,
                  args.workers, args.limit, errors=args.errors)
    return 0


if __name__ == "__main__":
    sys.exit(main())
