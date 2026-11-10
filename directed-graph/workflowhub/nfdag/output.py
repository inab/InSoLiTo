"""Writing the DAGs: nodes.csv, edges.csv and warnings.log per workflow, and the overview CSV."""

import csv
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Final, Self

from .build import Result
from .process import OUTPUT_FIELDS

# one row per tool node: the tool first, then everything known about its process
NODE_FIELDS: Final = (
    "node",
    "process_node",
    "step",
    "tool",
    "tool_source",
    "declared_tool",
    "meta_biotools_id",
    *OUTPUT_FIELDS,
)
EDGE_FIELDS: Final = ("source", "target", "channel", "kind")


@dataclass(slots=True)
class OverviewRow:
    """One row of the overview CSV; the counts are None for a workflow that failed."""

    workflow: str
    dsl: str  # dsl1 | dsl2 | error
    processes_defined: int | None = None
    nodes: int | None = None  # process nodes
    tool_nodes: int | None = None  # after splitting processes into the tools they run
    edges: int | None = None  # between tool nodes
    unresolved: int | None = None  # number of warnings

    @classmethod
    def of(cls, workflow: str, result: Result) -> Self:
        return cls(
            workflow,
            result.dsl,
            result.processes_defined,
            len(result.graph.nodes),
            len(result.tools.nodes),
            len(result.tools.edges),
            len(result.warnings),
        )


def write_dag(out_dir: Path, result: Result) -> None:
    """nodes.csv, edges.csv and warnings.log of one workflow."""
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "nodes.csv").open("w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=NODE_FIELDS)
        writer.writeheader()
        for node, tool in sorted(result.tools.nodes.items(), key=lambda item: item[0]):
            info = result.pipe.process_info(tool.source, tool.process)
            writer.writerow(
                {
                    "node": node,
                    "process_node": tool.process_node,
                    "step": tool.index,
                    "tool": tool.step.tool,
                    "tool_source": tool.step.source,
                    "declared_tool": tool.step.declared,
                    "meta_biotools_id": tool.step.meta_biotools_id,
                    **info.row(),
                }
            )
    with (out_dir / "edges.csv").open("w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(EDGE_FIELDS)
        for (a, b), (channels, kind) in sorted(result.tools.edges.items()):
            writer.writerow([a, b, ";".join(sorted(channels)), kind])
    (out_dir / "warnings.log").write_text("".join(w + "\n" for w in result.warnings))


def write_error(out_dir: Path, text: str) -> Path:
    """error.log of a workflow that could not be read; returns its path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "error.log"
    path.write_text(text)
    return path


def write_overview(path: Path, rows: list[OverviewRow]) -> None:
    with path.open("w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=[f.name for f in fields(OverviewRow)])
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
