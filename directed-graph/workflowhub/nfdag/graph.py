"""The process DAG of one workflow."""

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .sources import Source

Node = str  # qualified like Nextflow's names, e.g. `PREPARE_DATA:CHECKM2`
Producer = tuple[Node, str]  # (node, output channel)
Producers = set[Producer]


@dataclass(slots=True)
class Graph:
    """Process nodes, and edges between them labelled with the channels they carry."""

    nodes: dict[Node, tuple["Source", str]] = field(default_factory=dict)  # node -> (file, process name)
    edges: dict[tuple[Node, Node], set[str]] = field(default_factory=dict)  # (source, target) -> channels

    def add_node(self, node: Node, source: "Source", process: str) -> None:
        self.nodes.setdefault(node, (source, process))

    def connect(self, producers: Iterable[Producer], target: Node) -> list[Node]:
        """Add edges producer -> target; returns the producers left out because the edge would close a cycle.
        A process runs once per workflow, so a cycle only comes from reading alternative branches together
        (the same process called in two `if` blocks, the second time fed by the first one's results)."""
        skipped = []
        for producer, channel in producers:
            if producer == target:
                continue
            if (producer, target) not in self.edges and self._reaches(target, producer):
                skipped.append(producer)
                continue
            self.edges.setdefault((producer, target), set()).add(channel)
        return skipped

    def _reaches(self, start: Node, goal: Node) -> bool:
        """Whether a path of edges leads from start to goal."""
        successors: dict[Node, list[Node]] = {}
        for a, b in self.edges:
            successors.setdefault(a, []).append(b)
        seen, todo = {start}, [start]
        while todo:
            for nxt in successors.get(todo.pop(), ()):
                if nxt == goal:
                    return True
                if nxt not in seen:
                    seen.add(nxt)
                    todo.append(nxt)
        return False
