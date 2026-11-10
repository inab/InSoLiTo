"""Writing the DAGs: nodes.csv, edges.csv and warnings.log per workflow, and the overview CSV."""

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final, Self

from .build import Result
from .process import OUTPUT_FIELDS

NODE_FIELDS: Final = ("node", *OUTPUT_FIELDS)


@dataclass(slots=True)
class OverviewRow:
    """One row of the overview CSV; the counts are None for a workflow that failed."""

    workflow: str
    dsl: str  # dsl1 | dsl2 | error
    processes_defined: int | None = None
    nodes: int | None = None
    edges: int | None = None
    unresolved: int | None = None  # number of warnings

    @classmethod
    def of(cls, workflow: str, result: Result) -> Self:
        return cls(
            workflow,
            result.dsl,
            result.processes_defined,
            len(result.graph.nodes),
            len(result.graph.edges),
            len(result.warnings),
        )


def write_dag(out_dir: Path, result: Result) -> None:
    """nodes.csv, edges.csv and warnings.log of one workflow."""
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "nodes.csv").open("w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=NODE_FIELDS)
        writer.writeheader()
        for node, (source, process) in sorted(result.graph.nodes.items(), key=lambda item: item[0]):
            writer.writerow({"node": node, **result.pipe.process_info(source, process).row()})
    with (out_dir / "edges.csv").open("w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(["source", "target", "channel"])
        for (a, b), channels in sorted(result.graph.edges.items()):
            writer.writerow([a, b, ";".join(sorted(channels))])
    (out_dir / "warnings.log").write_text("".join(w + "\n" for w in result.warnings))


def write_error(out_dir: Path, text: str) -> Path:
    """error.log of a workflow that could not be read; returns its path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "error.log"
    path.write_text(text)
    return path


def write_overview(path: Path, rows: list[OverviewRow]) -> None:
    with path.open("w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(
            out, fieldnames=["workflow", "dsl", "processes_defined", "nodes", "edges", "unresolved"]
        )
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
