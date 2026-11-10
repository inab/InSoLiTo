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

    def connect(self, producers: Iterable[Producer], target: Node) -> None:
        for producer, channel in producers:
            if producer != target:
                self.edges.setdefault((producer, target), set()).add(channel)
