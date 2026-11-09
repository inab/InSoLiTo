"""Download the complete Europe PMC Open Access full-text corpus from the bulk dump.

``download_europepmc.py`` makes one API call per paper. That is fine for a few topics,
but would take ~11 days for the whole OA corpus (~7.4M papers with a reference list).
EBI publishes the same JATS XML as ~1,300 bundles of ``<articles><article>...``
(~173 GB gzipped, regenerated weekly) at https://ftp.ebi.ac.uk/pub/databases/pmc/oa/.

Three steps, all resumable:

1. list      - read the directory index and HEAD every bundle for its exact size.
               Kept in ``<out>/bulk/bundles.tsv``, which is also the progress record.
2. download  - fetch bundles into ``<out>/bulk/oa/``. An interrupted download resumes
               from its ``.part`` file with an HTTP Range request.
3. split     - stream each bundle and write every article to the layout the topic
               downloader uses, ``<out>/xml/PMCxxx/PMCxxxxxxx.xml.gz``, so
               parse_jats.py runs unchanged. Articles without a reference list are
               skipped (like the API's ``HAS_REFLIST:Y``). One manifest row per article
               goes to ``<out>/bulk/manifest.tsv``.

With ``--step all`` (default) bundles are split while later ones are still downloading,
and each bundle is deleted once it is split (``--keep-bundles`` keeps them).

Re-running later only re-processes bundles whose size changed since they were last
split (every bundle gets a new timestamp each week, so size is the change signal).
Articles from a changed bundle are overwritten, as it may carry corrections.

Example::

    python download_europepmc_bulk.py --limit 2 --out /tmp/oa_test   # smoke test
    python download_europepmc_bulk.py --contact you@example.org      # full corpus
"""

from __future__ import annotations

import argparse
import csv
import gzip
import logging
import os
import re
import signal
import sys
import threading
import time
import zlib
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, ThreadPoolExecutor, wait
from dataclasses import asdict, dataclass, fields
from pathlib import Path

import requests
from lxml import etree

import download_europepmc as dl

logger = logging.getLogger("europepmc_bulk")

OA_URL = "https://ftp.ebi.ac.uk/pub/databases/pmc/oa/"
BUNDLE_RE = re.compile(r'href="(PMC(\d+)_PMC\d+\.xml\.gz)"')
TOPIC = "oa_bulk"  # value of the manifest's `topics` column
CHUNK = 1 << 20

# Set on Ctrl+C / SIGTERM so download threads stop between chunks (the .part file is kept).
_STOP = threading.Event()


# --------------------------------------------------------------------------- #
# State: one row per bundle in bundles.tsv
# --------------------------------------------------------------------------- #


@dataclass
class Bundle:
    name: str
    size: int = 0                  # remote size in bytes, from the last listing
    etag: str = ""                 # for If-Range, so a resume never mixes two versions
    split_size: int | None = None  # size of the bundle version that was last split
    n_articles: int = 0
    n_written: int = 0
    n_existing: int = 0            # already on disk (e.g. from the topic downloader)
    n_no_reflist: int = 0
    n_no_pmcid: int = 0
    status: str = ""               # "" or "error: ..."

    @property
    def needs_split(self) -> bool:
        return self.split_size != self.size


def bundle_key(name: str) -> int:
    """PMC13900_PMC17829.xml.gz -> 13900, so bundles sort by PMCID, not alphabetically."""
    return int(BUNDLE_RE.match(f'href="{name}"').group(2))


def load_state(path: Path) -> dict[str, Bundle]:
    if not path.exists():
        return {}
    state = {}
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            b = state[row["name"]] = Bundle(row["name"], etag=row["etag"], status=row["status"])
            for f in fields(Bundle):
                if f.name not in ("name", "etag", "status") and row[f.name]:
                    setattr(b, f.name, int(row[f.name]))
    return state


def save_state(path: Path, state: dict[str, Bundle]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tsv.part")
    with tmp.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=[f.name for f in fields(Bundle)], delimiter="\t")
        writer.writeheader()
        for name in sorted(state, key=bundle_key):
            row = asdict(state[name])
            row["split_size"] = "" if row["split_size"] is None else row["split_size"]
            writer.writerow(row)
    tmp.replace(path)


# --------------------------------------------------------------------------- #
# Step 1: list
# --------------------------------------------------------------------------- #


def list_bundles(state: dict[str, Bundle], user_agent: str, workers: int, limit: int | None) -> list[str]:
    """Refresh sizes in ``state`` from the server. Returns the bundle names to process."""
    session = dl.get_session(user_agent)
    resp = session.get(OA_URL, timeout=120)
    resp.raise_for_status()
    names = sorted({m.group(1) for m in BUNDLE_RE.finditer(resp.text)}, key=bundle_key)
    if not names:
        raise SystemExit(f"No bundles found in the directory index at {OA_URL}")
    for gone in set(state) - set(names):
        del state[gone]  # merged into other bundles upstream; its articles live on there
    if limit:
        names = names[:limit]

    def head(name: str) -> tuple[str, int, str]:
        r = dl.get_session(user_agent).head(OA_URL + name, timeout=60)
        r.raise_for_status()
        return name, int(r.headers["Content-Length"]), r.headers.get("ETag", "")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for name, size, etag in pool.map(head, names):
            b = state.setdefault(name, Bundle(name))
            b.size, b.etag = size, etag
    n_todo = sum(state[n].needs_split for n in names)
    total_gb = sum(state[n].size for n in names) / 1e9
    logger.info("%d bundles (%.1f GB) listed; %d new or changed", len(names), total_gb, n_todo)
    return names


# --------------------------------------------------------------------------- #
# Step 2: download
# --------------------------------------------------------------------------- #


def download_bundle(b: Bundle, dest: Path, user_agent: str, attempts: int = 5) -> tuple[str, int]:
    """Download one bundle, resuming from ``<dest>.part``. Returns (status, size)."""
    session = dl.get_session(user_agent)
    part = dest.with_name(dest.name + ".part")
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_error = ""
    for attempt in range(attempts):
        if _STOP.is_set():
            return "error: interrupted", b.size
        have = part.stat().st_size if part.exists() else 0
        headers = {"Range": f"bytes={have}-", "If-Range": b.etag} if have and b.etag else {}
        try:
            with session.get(OA_URL + b.name, headers=headers, stream=True, timeout=(30, 300)) as resp:
                if resp.status_code == 206:  # resuming the same version
                    total = int(resp.headers["Content-Range"].rsplit("/", 1)[1])
                    mode = "ab"
                elif resp.status_code == 200:  # fresh start, or the file changed upstream
                    total = int(resp.headers["Content-Length"])
                    mode = "wb"
                elif resp.status_code == 416 and have == b.size:  # .part is already complete
                    total, mode = b.size, None
                else:
                    raise requests.HTTPError(f"HTTP {resp.status_code}")
                if mode:
                    with part.open(mode) as fh:
                        for chunk in resp.iter_content(CHUNK):
                            if _STOP.is_set():
                                return "error: interrupted", b.size
                            fh.write(chunk)
            got = part.stat().st_size
            if got == total:
                part.replace(dest)
                return "ok", total
            last_error = f"size {got} != {total}"
            if got > total:
                part.unlink()
        except (requests.RequestException, OSError, KeyError, ValueError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        logger.warning("%s attempt %d/%d failed: %s", b.name, attempt + 1, attempts, last_error)
        time.sleep(2 ** attempt)
    return f"error: {last_error}", b.size


# --------------------------------------------------------------------------- #
# Step 3: split
# --------------------------------------------------------------------------- #


def _text(elem, path: str) -> str:
    e = elem.find(path)
    return "".join(e.itertext()).strip() if e is not None else ""


def article_meta(article) -> dict[str, str]:
    """IDs and manifest fields from a JATS <article>'s front matter."""
    ids: dict[str, str] = {}
    for a in article.iterfind("front/article-meta/article-id"):
        ids.setdefault(a.get("pub-id-type", ""), (a.text or "").strip())
    pmcid = ids.get("pmcid", "")
    if not pmcid and ids.get("pmcaid", "").isdigit():
        pmcid = "PMC" + ids["pmcaid"]
    if pmcid and not pmcid.startswith("PMC"):
        pmcid = "PMC" + pmcid
    return {
        "pmcid": pmcid,
        "pmid": ids.get("pmid", ""),
        "doi": ids.get("doi", ""),
        "pub_type": article.get("article-type", ""),
        "pub_year": _text(article, "front/article-meta/pub-date/year"),
        "journal": (_text(article, "front/journal-meta/journal-title-group/journal-title")
                    or _text(article, "front/journal-meta/journal-title")),
    }


def split_bundle(bundle_path: str, xml_dir: str, manifest_part: str,
                 overwrite: bool, require_reflist: bool) -> dict[str, int]:
    """Write each <article> in a bundle to its own .xml.gz. Runs in a worker process.

    Also writes this bundle's manifest rows (no header) to ``manifest_part``, last and
    atomically, so a half-split bundle never leaves a partial manifest behind.
    """
    xml_dir_p = Path(xml_dir)
    counts = dict(n_articles=0, n_written=0, n_existing=0, n_no_reflist=0, n_no_pmcid=0)
    rows = []
    with gzip.open(bundle_path, "rb") as fh:
        for _, article in etree.iterparse(fh, events=("end",), tag="article", huge_tree=True):
            parent = article.getparent()
            if parent is None or parent.getparent() is not None:
                continue  # only the top-level <article>s of <articles>
            counts["n_articles"] += 1
            meta = article_meta(article)
            pmcid = meta["pmcid"]
            if not re.fullmatch(r"PMC\d+", pmcid):
                counts["n_no_pmcid"] += 1
            elif require_reflist and article.find(".//ref-list") is None:
                counts["n_no_reflist"] += 1
            else:
                dest = dl.xml_path(xml_dir_p, pmcid)
                if not overwrite and dest.exists() and dest.stat().st_size > 0:
                    counts["n_existing"] += 1
                else:
                    body = etree.tostring(article, encoding="UTF-8", xml_declaration=True, with_tail=False)
                    dl.write_gz_atomic(dest, body)
                    counts["n_written"] += 1
                row = {**meta, "topics": TOPIC, "status": "ok",
                       "xml_path": str(dest.relative_to(xml_dir_p.parent))}
                rows.append([row[c] for c in dl.MANIFEST_COLUMNS])
            # Free what we've processed: keeps memory flat on 100+ MB bundles.
            article.clear(keep_tail=False)
            while article.getprevious() is not None:
                del parent[0]

    part = Path(manifest_part)
    part.parent.mkdir(parents=True, exist_ok=True)
    tmp = part.with_suffix(".tsv.part")
    with tmp.open("w", newline="") as out:
        csv.writer(out, delimiter="\t").writerows(rows)
    tmp.replace(part)
    return counts


def write_manifest(names: list[str], parts_dir: Path, manifest_file: Path) -> int:
    """Concatenate the per-bundle manifest parts, in PMCID order. Returns the row count."""
    tmp = manifest_file.with_suffix(".tsv.part")
    n = 0
    with tmp.open("w", newline="") as out:
        csv.writer(out, delimiter="\t").writerow(dl.MANIFEST_COLUMNS)
        for name in sorted(names, key=bundle_key):
            part = parts_dir / name.replace(".xml.gz", ".tsv")
            if part.exists():
                with part.open() as fh:
                    for line in fh:
                        out.write(line)
                        n += 1
    tmp.replace(manifest_file)
    return n


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #


def run(args: argparse.Namespace, user_agent: str) -> None:
    bulk_dir = args.out / "bulk"
    bundle_dir = bulk_dir / "oa"
    parts_dir = bulk_dir / "manifest_parts"
    xml_dir = args.out / "xml"
    state_file = bulk_dir / "bundles.tsv"
    state = load_state(state_file)

    if args.step in ("list", "all"):
        names = list_bundles(state, user_agent, args.workers, args.limit)
        save_state(state_file, state)
        if args.step == "list":
            return
    else:
        if not state:
            raise SystemExit(f"No bundle list at {state_file}. Run --step list first.")
        names = sorted(state, key=bundle_key)[: args.limit or None]

    do_download = args.step in ("download", "all")
    do_split = args.step in ("split", "all")
    todo = [state[n] for n in names if state[n].needs_split or (args.refresh and do_split)]

    def on_disk(b: Bundle) -> bool:
        p = bundle_dir / b.name
        return p.exists() and p.stat().st_size == b.size

    dl_pool = ThreadPoolExecutor(max_workers=args.workers)
    split_pool = ProcessPoolExecutor(max_workers=args.split_workers) if do_split else None
    futures: dict = {}  # future -> ("download" | "split", Bundle)

    def submit_split(b: Bundle) -> None:
        # A bundle that was split before at another size has changed upstream: overwrite.
        overwrite = args.refresh or b.split_size is not None
        fut = split_pool.submit(split_bundle, str(bundle_dir / b.name), str(xml_dir),
                                str(parts_dir / b.name.replace(".xml.gz", ".tsv")),
                                overwrite, not args.include_no_reflist)
        futures[fut] = ("split", b)

    n_ready = n_missing = 0
    for b in todo:
        if on_disk(b):
            if do_split:
                submit_split(b)
                n_ready += 1
        elif do_download:
            futures[dl_pool.submit(download_bundle, b, bundle_dir / b.name, user_agent)] = ("download", b)
        else:
            n_missing += 1
    gb = sum(b.size for _, b in futures.values()) / 1e9
    logger.info("%d bundles to process (%.1f GB): %d already downloaded, %d to download%s",
                len(futures), gb, n_ready, len(futures) - n_ready,
                f"; {n_missing} not downloaded yet (run --step download)" if n_missing else "")

    totals: dict[str, int] = {}
    n_done = n_err = 0
    n_total = len(futures)
    t0 = time.time()
    try:
        while futures:
            done, _ = wait(futures, return_when=FIRST_COMPLETED)
            for fut in done:
                kind, b = futures.pop(fut)
                if kind == "download":
                    status, size = fut.result()
                    if status != "ok":
                        logger.warning("%s download failed: %s", b.name, status)
                        b.status = status
                        n_done += 1
                        n_err += 1
                        continue
                    b.size, b.status = size, ""
                    logger.info("%s downloaded (%.0f MB)", b.name, size / 1e6)
                    if do_split:
                        submit_split(b)
                    else:
                        n_done += 1
                    continue

                n_done += 1
                bundle = bundle_dir / b.name
                try:
                    counts = fut.result()
                except (EOFError, OSError, zlib.error, etree.XMLSyntaxError) as exc:
                    # Corrupt or truncated bundle: drop it so the next run downloads it again.
                    b.status = f"error: {type(exc).__name__}: {exc}"[:300]
                    logger.warning("%s split failed (%s); deleting it for re-download", b.name, b.status)
                    bundle.unlink(missing_ok=True)
                    n_err += 1
                    continue
                for k, v in counts.items():
                    setattr(b, k, v)
                    totals[k] = totals.get(k, 0) + v
                b.split_size, b.status = b.size, ""
                if not args.keep_bundles:
                    bundle.unlink(missing_ok=True)
                save_state(state_file, state)
                el = time.time() - t0
                logger.info("[%d/%d] %s split: %s  (total %s, ETA %.0f min)", n_done, n_total, b.name,
                            counts, totals, el / n_done * (n_total - n_done) / 60)
    except KeyboardInterrupt:
        _STOP.set()
        logger.warning("Interrupted - saving progress before exiting. Re-run the same command to resume.")
        raise
    finally:
        dl_pool.shutdown(wait=True, cancel_futures=True)
        if split_pool:
            split_pool.shutdown(wait=True, cancel_futures=True)
        save_state(state_file, state)
        if do_split:
            n = write_manifest(list(state), parts_dir, bulk_dir / "manifest.tsv")
            logger.info("Manifest: %d articles -> %s", n, bulk_dir / "manifest.tsv")
    logger.info("Done: %d bundles, %d failed. %s", n_done, n_err, totals)
    if n_err:
        logger.info("Failed bundles are listed in %s (status column); re-run to retry them.", state_file)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, default=Path(__file__).parent / "data",
                   help="Output directory, shared with download_europepmc.py (default: DB/CoCitation/data).")
    p.add_argument("--step", choices=["list", "download", "split", "all"], default="all")
    p.add_argument("--workers", type=int, default=4,
                   help="Parallel bundle downloads (default: 4). Bundles are large, so a few are enough.")
    p.add_argument("--split-workers", type=int, default=min(8, os.cpu_count() or 1),
                   help="Processes splitting bundles into articles (default: min(8, CPUs)).")
    p.add_argument("--limit", type=int, default=None,
                   help="Only the first N bundles, by PMCID (for smoke tests; the first ones are small).")
    p.add_argument("--keep-bundles", action="store_true",
                   help="Keep the downloaded bundles after splitting (another ~173 GB).")
    p.add_argument("--refresh", action="store_true",
                   help="Re-split every bundle and overwrite article files already on disk.")
    p.add_argument("--include-no-reflist", action="store_true",
                   help="Also write articles without a <ref-list> (skipped by default).")
    p.add_argument("--contact", default="",
                   help="Contact email added to the User-Agent so EBI can reach you if needed.")
    p.add_argument("--ca-bundle", default=None,
                   help="Path to a PEM CA bundle (e.g. your corporate root CA) to verify TLS against.")
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
    # Treat `kill <pid>` (SIGTERM) like Ctrl+C, so progress is still saved.
    signal.signal(signal.SIGTERM, _raise_keyboard_interrupt)
    dl._CA_BUNDLE = args.ca_bundle
    user_agent = "BH2026-InSoLiTo co-citation harvester (bulk)"
    if args.contact:
        user_agent += f" (mailto:{args.contact})"
    _lock = dl.acquire_run_lock(args.out)  # noqa: F841 - same lock as the topic downloader
    run(args, user_agent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
