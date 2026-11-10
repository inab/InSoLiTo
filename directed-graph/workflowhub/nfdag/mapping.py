"""Map the tool nodes of the Nextflow DAGs to bio.tools IDs, and translate the DAG edges into bio.tools edges.

The bio.tools ID of a tool node, first match wins (the method is recorded):
  curated  the hand-curated TSV (nextflow_curated_map.tsv): `map` to one or more IDs (several make a chain),
           or `drop` (not a bio.tools tool: the node goes, its neighbours are connected)
  meta     the `biotools:` identifier an nf-core-style meta.yml gives for this tool
  codex    the Galaxy Codex: the tool as a bioconda package, or as a Galaxy suite or tool ID
  name     the tool name is itself a bio.tools ID (also with '_' / '-' swapped, without .py, .sh, .exe)
  prefix   only for processes that stand for their own scripts: the part of the process name before '_'
           (SAMTOOLS_SORT -> samtools), not for generic words
Anything else is unmapped: the node is removed with its edges (a gap, like Galaxy tools without an ID)
and the tool is listed for curation.
"""

import csv
import itertools
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Literal

Action = Literal["map", "drop", "unmapped"]

SCRIPT_SUFFIXES: Final = (".py", ".sh", ".pl", ".r", ".exe", ".jar")
CURATED_FIELDS: Final = ("tool", "action", "biotoolsID", "note")


@dataclass(slots=True)
class CuratedEntry:
    """One row of the curated TSV."""

    action: Literal["map", "drop"]
    ids: list[str]
    note: str


def read_curated(path: Path) -> dict[str, CuratedEntry]:
    """The curated TSV: lower-case tool name -> entry. Lines starting with '#' are comments."""
    if not path.exists():
        return {}
    entries: dict[str, CuratedEntry] = {}
    with path.open(encoding="utf-8") as f:
        lines = [(n, line) for n, line in enumerate(f, 1) if line.strip() and not line.startswith("#")]
    reader = csv.DictReader((line for _, line in lines), delimiter="\t")
    for (number, _), row in zip(lines[1:], reader, strict=True):
        tool = (row.get("tool") or "").strip().lower()
        action = (row.get("action") or "").strip().lower()
        ids = [i.strip() for i in (row.get("biotoolsID") or "").split(";") if i.strip()]
        if not tool:
            continue
        if action == "map" and ids:
            entries[tool] = CuratedEntry("map", ids, row.get("note") or "")
        elif action == "drop":
            entries[tool] = CuratedEntry("drop", [], row.get("note") or "")
        elif action == "map":
            raise ValueError(f"{path.name} line {number}: {tool!r} has action map but no biotoolsID")
        else:
            raise ValueError(f"{path.name} line {number}: action of {tool!r} must be map or drop, not {action!r}")
    return entries


def tool_key(name: str) -> str:
    """A tool name for lookups: lower case, without script suffixes."""
    key = name.lower()
    for suffix in SCRIPT_SUFFIXES:
        key = key.removesuffix(suffix)
    return key


@dataclass(slots=True)
class ToolMap:
    """The bio.tools mapping of one tool node."""

    action: Action
    ids: list[str] = field(default_factory=list)  # several for a curated chain
    method: str = ""  # curated | meta | codex | name | prefix
    codex_id: str = ""  # the candidates, to spot disagreements
    name_id: str = ""


@dataclass(slots=True)
class Lookup:
    """Everything a tool name can be mapped with."""

    biotools_ids: dict[str, str]  # lower case -> real spelling
    codex_conda: dict[str, str]  # bioconda package -> bio.tools ID
    codex_name: dict[str, str]  # Galaxy suite or tool ID -> bio.tools ID
    curated: dict[str, CuratedEntry]
    variants: Callable[[str], set[str]]  # spellings to try (map_galaxy_tools.variants)
    prefix_blocklist: set[str]

    def spelled(self, biotools_id: str) -> str:
        """A bio.tools ID in its real spelling, if known."""
        return self.biotools_ids.get(biotools_id.lower(), biotools_id)

    def _candidates(self, name: str) -> tuple[str, str]:
        """(codex ID, name ID) of a tool name, each '' if not found."""
        key = tool_key(name)
        codex_id = self.codex_conda.get(key) or self.codex_name.get(key, "")
        name_id = next((self.biotools_ids[v] for v in sorted(self.variants(key)) if v in self.biotools_ids), "")
        return codex_id, name_id

    def map(self, tool: str, source: str, meta_id: str, process: str, declared: str = "") -> ToolMap:
        """Map one tool node; source is how the tool name was found (executable, meta, ..., process),
        declared the tool the module declares for it (bowtie2-build -> bowtie2), tried after the tool itself."""
        curated = self.curated.get(tool.lower()) or self.curated.get(declared.lower())
        if curated:
            return ToolMap(curated.action, [self.spelled(i) for i in curated.ids], "curated")
        codex_id, name_id = self._candidates(tool)
        if not codex_id and not name_id and declared and declared.lower() != tool.lower():
            codex_id, name_id = self._candidates(declared)
        found = ToolMap("map", codex_id=codex_id, name_id=name_id)
        if meta_id:
            found.ids, found.method = [self.spelled(meta_id.removeprefix("biotools:"))], "meta"
        elif codex_id:
            found.ids, found.method = [codex_id], "codex"
        elif name_id:
            found.ids, found.method = [name_id], "name"
        elif source == "process":
            first = process.lower().split("_")[0]
            if first != process.lower() and first not in self.prefix_blocklist and first in self.biotools_ids:
                found.ids, found.method = [self.biotools_ids[first]], "prefix"
        if not found.ids:
            found.action = "unmapped"
        return found


@dataclass(slots=True)
class BiotoolsPair:
    """One bio.tools edge of one workflow."""

    source: str
    target: str
    kind: str  # dag | chain (inside one process, or a curated chain) | bridged (through dropped tools)
    source_node: str
    target_node: str


def translate(mapped: dict[str, ToolMap], edges: list[tuple[str, str, str]]) -> tuple[list[BiotoolsPair], int]:
    """bio.tools edges of one workflow from its tool nodes and (source, target, kind) edges,
    and the number of DAG edges lost because a side is unmapped."""
    successors: dict[str, list[tuple[str, str]]] = {}
    for a, b, kind in edges:
        successors.setdefault(a, []).append((b, kind))

    def reached(node: str) -> Iterator[tuple[str, str]]:
        """Mapped nodes after node, walking through dropped ones; (node, kind)."""
        seen, todo = {node}, [(b, kind) for b, kind in successors.get(node, [])]
        while todo:
            nxt, kind = todo.pop()
            if nxt in seen:
                continue
            seen.add(nxt)
            if mapped[nxt].action == "map":
                yield nxt, kind
            elif mapped[nxt].action == "drop":
                todo += [(b, "bridged") for b, _ in successors.get(nxt, [])]

    pairs = []
    for node, m in mapped.items():
        if m.action != "map":
            continue
        for a, b in itertools.pairwise(m.ids):
            pairs.append(BiotoolsPair(a, b, "chain", node, node))
        for nxt, kind in reached(node):
            pairs.append(BiotoolsPair(m.ids[-1], mapped[nxt].ids[0], kind, node, nxt))
    lost = sum(1 for a, b, _ in edges if "unmapped" in (mapped[a].action, mapped[b].action))
    # like Galaxy: samtools_view -> samtools_sort is no edge, both are the same bio.tools node
    return [p for p in pairs if p.source != p.target], lost
