"""Split the process DAG into tool nodes: a process running several tools becomes a chain of them."""

import itertools
from dataclasses import dataclass, field
from pathlib import Path

from .graph import Graph, Node
from .process import Step
from .sources import Pipeline, Source


@dataclass(slots=True)
class ToolNode:
    """One tool of one process node."""

    process_node: Node  # the process node of the DAG, e.g. ALIGN:BWA_MEM
    index: int  # position in the process's chain, from 1
    step: Step
    source: Source
    process: str  # the process name as defined


@dataclass(slots=True)
class ToolGraph:
    """Tool nodes and their edges: `dag` edges between processes, `chain` edges inside one process."""

    nodes: dict[Node, ToolNode] = field(default_factory=dict)
    edges: dict[tuple[Node, Node], tuple[set[str], str]] = field(default_factory=dict)  # -> (channels, kind)


def read_excluded(path: Path | None) -> frozenset[str]:
    """The exclusion list: one tool per line (lower case, glob patterns like `r-*` allowed), `#` starts a comment."""
    if path is None or not path.exists():
        return frozenset()
    names = (line.split("#")[0].strip().lower() for line in path.read_text(encoding="utf-8").splitlines())
    return frozenset(n for n in names if n)


def expand(graph: Graph, pipe: Pipeline) -> ToolGraph:
    """Replace each process node by its steps (named `<process node>/<tool>`) and rewire the edges:
    an edge A -> B goes from the last tool of A to the first tool of B."""
    tools = ToolGraph()
    chains: dict[Node, list[Node]] = {}
    for process_node, (source, process) in graph.nodes.items():
        chain = []
        for index, step in enumerate(pipe.process_info(source, process).steps, 1):
            node = f"{process_node}/{step.tool}"
            if node in tools.nodes:  # the same tool twice in one process (bwa index ... bwa mem)
                continue
            tools.nodes[node] = ToolNode(process_node, index, step, source, process)
            chain.append(node)
        chains[process_node] = chain
        for a, b in itertools.pairwise(chain):
            tools.edges[(a, b)] = (set(), "chain")
    for (a, b), channels in graph.edges.items():
        tools.edges[(chains[a][-1], chains[b][0])] = (channels, "dag")
    return tools
