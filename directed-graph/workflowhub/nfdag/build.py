"""Build the DAG of one downloaded workflow: choose DSL1 or DSL2 and the entry workflow(s)."""

import re
from dataclasses import dataclass
from pathlib import Path

from .dsl1 import dsl1_graph
from .dsl2 import Dsl2
from .graph import Graph
from .sources import Pipeline, Source
from .steps import ToolGraph, expand

Entry = tuple[Source, str | None]  # (file, workflow name; None for the unnamed entry workflow)


@dataclass(slots=True)
class Result:
    """The DAG of one workflow, with what is needed to write it out."""

    pipe: Pipeline
    graph: Graph  # process nodes
    tools: ToolGraph  # the same DAG with each process split into the tools it runs
    dsl: str  # dsl1 | dsl2

    @property
    def warnings(self) -> list[str]:
        return self.pipe.warnings

    @property
    def processes_defined(self) -> int:
        return sum(len(s.processes) for s in self.pipe.sources.values())


def _unnamed_entries(pipe: Pipeline) -> list[Entry]:
    """Unnamed `workflow {}` blocks of files that no other file includes."""
    # an unnamed `workflow {}` in a file that other files include only makes that file runnable on its own
    included = {pipe.include_file(s, target) for s in pipe.sources.values() for _, target in s.includes.values()}
    return [(s, None) for s in pipe.sources.values() if None in s.workflows and s.path not in included]


def _uncalled_workflows(pipe: Pipeline) -> list[Entry]:
    """Named workflows that no other workflow calls (for pipelines without an unnamed entry workflow)."""
    called = set()
    for s in pipe.sources.values():
        for n in re.findall(r"\b(\w+)\s*\(", s.code):
            resolved = pipe.resolve(s, n)
            if resolved and resolved[0] == "workflow":
                called.add(resolved[1:])
    return [(s, n) for s in pipe.sources.values() for n in s.workflows if (s, n) not in called]


def _main_entries(root: Path, entries: list[Entry]) -> list[Entry]:
    """The entry script is the one nearest the top folder (not e.g. tests/main.nf), main.nf if possible."""
    top = min(len(s.path.relative_to(root).parts) for s, _ in entries)
    entries = [e for e in entries if len(e[0].path.relative_to(root).parts) == top]
    return [e for e in entries if e[0].path.name == "main.nf"] or entries


def _all_processes(pipe: Pipeline, graph: Graph, *, unique: bool) -> None:
    """Fallback: every defined process as a node without edges."""
    for s in pipe.sources.values():
        for p in s.processes:
            graph.add_node(f"{p}@{s.rel}" if unique and p in graph.nodes else p, s, p)


def build(root: Path, excluded_tools: frozenset[str] = frozenset()) -> Result:
    """Read all files of a downloaded workflow and build its DAG; excluded_tools never become tool nodes."""
    pipe = Pipeline(root, excluded_tools)
    graph = Graph()
    entries = _unnamed_entries(pipe)
    has_dsl1 = any(
        pipe.process_info(s, p).into or pipe.process_info(s, p).takes_from
        for s in pipe.sources.values()
        for p in s.processes
    )
    if entries:
        dsl = "dsl2"
    elif has_dsl1:
        dsl = "dsl1"
    else:
        dsl = "dsl2"
        entries = _uncalled_workflows(pipe)
        if not entries:
            pipe.warn("no workflow block and no DSL1 channels: processes listed without edges")
            _all_processes(pipe, graph, unique=False)

    if dsl == "dsl1":
        dsl1_graph(pipe, graph)
    elif entries:
        dsl2 = Dsl2(pipe, graph)
        for source, name in _main_entries(root, entries):
            dsl2.run_workflow(source, name, f"{name}:" if name else "", [])
    if not graph.nodes:
        pipe.warn("no process reached from the entry workflow: all processes listed without edges")
        _all_processes(pipe, graph, unique=True)
    return Result(pipe=pipe, graph=graph, tools=expand(graph, pipe), dsl=dsl)
