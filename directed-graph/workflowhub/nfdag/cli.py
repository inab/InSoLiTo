"""Command line: build the DAG of every downloaded workflow (or of the --only ones)."""

import argparse
import sys
import traceback
from pathlib import Path
from typing import Final

from . import __doc__ as package_doc
from .build import build
from .output import OverviewRow, write_dag, write_error, write_overview
from .steps import read_excluded

DATA_DIR: Final = Path(__file__).resolve().parent.parent / "data"
NF_DIR: Final = DATA_DIR / "download" / "nextflow"  # from download_workflowhub_nextflow.py
DAG_DIR: Final = DATA_DIR / "nextflow"
OVERVIEW_NAME: Final = "nextflow_dags.csv"
EXCLUDED_FILE: Final = Path(__file__).resolve().parent.parent / "nextflow_excluded_tools.txt"


def _workflow_folders(nf_dir: Path, only: list[str] | None) -> list[Path]:
    """The downloaded workflow folders (<id>_v<version>), by ID."""
    roots = sorted((p for p in nf_dir.iterdir() if p.is_dir()), key=lambda p: int(p.name.split("_")[0]))
    return [r for r in roots if r.name in only] if only else roots


def _summary(rows: list[OverviewRow], out_dir: Path, overview: Path) -> str:
    done = [r for r in rows if r.dsl != "error"]
    return (
        f"Wrote {len(done)} DAGs to {out_dir}, overview in {overview}: "
        f"{sum(r.nodes or 0 for r in done)} process nodes, {sum(r.tool_nodes or 0 for r in done)} tool nodes, "
        f"{sum(r.edges or 0 for r in done)} edges, "
        f"{sum(1 for r in done if not r.edges)} workflows without edges, "
        f"{sum(1 for r in done if r.unresolved)} with warnings, {len(rows) - len(done)} failed (error.log)"
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=package_doc, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", action="append", help="only this workflow folder, e.g. 462_v3 (repeatable)")
    parser.add_argument("--verbose", action="store_true", help="print the warnings of each workflow")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DAG_DIR,
        help=f"where the DAGs go (default: data/nextflow), with the overview {OVERVIEW_NAME}",
    )
    parser.add_argument(
        "--exclude-file",
        type=Path,
        default=EXCLUDED_FILE,
        help="executables that never become tool nodes (default: nextflow_excluded_tools.txt)",
    )
    args = parser.parse_args(argv)

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    overview = out_dir / OVERVIEW_NAME
    excluded = read_excluded(args.exclude_file)
    rows: list[OverviewRow] = []
    for root in _workflow_folders(NF_DIR, args.only):
        try:
            result = build(root, excluded)
        except Exception:  # one unparsable workflow must not stop the run: keep the traceback
            path = write_error(out_dir / root.name, traceback.format_exc())
            print(f"  failed {root.name}: see {path}", file=sys.stderr)
            rows.append(OverviewRow(root.name, "error"))
            continue
        write_dag(out_dir / root.name, result)
        rows.append(OverviewRow.of(root.name, result))
        if args.verbose:
            print(
                f"{root.name}: {result.dsl}, {len(result.graph.nodes)} process nodes, "
                f"{len(result.tools.nodes)} tool nodes, {len(result.tools.edges)} edges"
            )
            for warning in result.warnings:
                print(f"  {warning}")

    write_overview(overview, rows)
    print(_summary(rows, out_dir, overview))
