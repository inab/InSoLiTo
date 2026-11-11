"""Map the tool nodes of the Nextflow DAGs to bio.tools entries, and translate the DAG edges into bio.tools edges.

The goal is a bio.tools entry for every tool that is not excluded or dropped. The reference is the full bio.tools
dump (biotools_raw*.jsonl): every ID used must exist in it. The bio.tools ID of a tool node, first match wins
(the method is recorded):
  curated        the hand-curated TSV (nextflow_curated_map.tsv): `map` to one or more IDs (several make a chain),
                 or `drop` (not a bio.tools tool: the node goes, its neighbours are connected)
  meta           the `biotools:` identifier an nf-core-style meta.yml gives for this tool, if it is in bio.tools
  biotools_id    the tool name is a bio.tools ID
  biotools_name  the tool name is the name of exactly one bio.tools entry
  biotools_url   the tool name is the package or repository name (GitHub, CRAN, Bioconductor, PyPI, ...)
                 in the links of exactly one bio.tools entry
  codex          the Galaxy Codex: the tool as a bioconda package or as a Galaxy suite
  prefix         only for processes that stand for their own scripts: the part of the process name before '_'
                 (SAMTOOLS_SORT -> samtools), not for generic words
The biotools_* methods also try the name without a bioconda group prefix (r-ggplot2 -> ggplot2); every method
tries the tool name first and then the package the module declares for it (bowtie2-build -> bowtie2).
Anything else is unmapped: the node is removed with its edges (a gap, like Galaxy tools without an ID)
and the tool is listed for curation, with suggestions from the dump.
"""

import csv
import difflib
import itertools
import json
import re
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Literal

Action = Literal["map", "drop", "unmapped"]

SCRIPT_SUFFIXES: Final = (".py", ".sh", ".pl", ".r", ".exe", ".jar")
CURATED_FIELDS: Final = ("tool", "action", "biotoolsID", "note")
GROUP_PREFIXES: Final = ("bioconductor-", "r-", "python-", "py-", "perl-")
MIN_URL_NAME: Final = 3  # shorter package / repository names are not matched (`s`, `t`)
# package or repository name in a URL of a bio.tools entry
URL_NAME: Final = re.compile(
    r"(?:github\.com|gitlab\.com|bitbucket\.org)/[^/\s]+/([\w.-]+)"
    r"|bioconductor\.org/packages/(?:[\w./-]*/)?html/([\w.]+?)\.html"
    r"|bioconductor\.org/packages/([\w.]+)/?$"
    r"|cran\.r-project\.org/(?:web/packages/|package=)([\w.]+)"
    r"|pypi\.org/project/([\w.-]+)"
    r"|anaconda\.org/bioconda/([\w.-]+)",
    re.IGNORECASE,
)


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
    key = name.lower().strip()
    for suffix in SCRIPT_SUFFIXES:
        key = key.removesuffix(suffix)
    return key


def spellings(key: str) -> list[str]:
    """Spellings of a lower-case name to look up: as is, with '_', '-' and ' ' swapped."""
    out = [key]
    for a, b in (("_", "-"), ("-", "_"), ("_", " "), ("-", " "), (" ", "-"), (" ", "_")):
        if a in key and key.replace(a, b) not in out:
            out.append(key.replace(a, b))
    return out


def _compact(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _words(name: str) -> set[str]:
    return {w for w in re.split(r"[^a-z0-9]+", name.lower()) if len(w) >= 4}


def ungrouped(key: str) -> str:
    """The name without a bioconda group prefix (bioconductor-complexheatmap -> complexheatmap), else ''."""
    return next((key[len(p) :] for p in GROUP_PREFIXES if key.startswith(p) and len(key) > len(p)), "")


@dataclass(slots=True)
class BiotoolsIndex:
    """The bio.tools dump, indexed for matching."""

    ids: dict[str, str] = field(default_factory=dict)  # lower case -> real spelling
    names: dict[str, str] = field(default_factory=dict)  # ID -> display name
    by_name: dict[str, str] = field(default_factory=dict)  # lower-case name, unique -> ID
    by_url: dict[str, str] = field(default_factory=dict)  # lower-case package / repository name, unique -> ID
    compact_ids: list[tuple[str, str]] = field(default_factory=list)  # (ID without '-', '_', ..., ID) for suggestions

    @classmethod
    def load(cls, path: Path) -> "BiotoolsIndex":
        """Read the bio.tools dump (one JSON entry per line)."""
        index = cls()
        name_ids: dict[str, set[str]] = defaultdict(set)
        url_ids: dict[str, set[str]] = defaultdict(set)
        with path.open(encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                biotools_id = entry["biotoolsID"]
                index.ids[biotools_id.lower()] = biotools_id
                name = (entry.get("name") or "").strip()
                index.names[biotools_id] = name
                for spelling in spellings(name.lower()):
                    name_ids[spelling].add(biotools_id)
                links = [entry.get("homepage") or ""] + [
                    (link or {}).get("url") or "" for link in (entry.get("link") or []) + (entry.get("download") or [])
                ]
                for url in links:
                    for match in URL_NAME.finditer(url.rstrip("/")):
                        package = next(g for g in match.groups() if g).lower().removesuffix(".git")
                        if len(package) >= MIN_URL_NAME:
                            url_ids[package].add(biotools_id)
        index.by_name = {n: next(iter(ids)) for n, ids in name_ids.items() if n and len(ids) == 1}
        index.by_url = {n: next(iter(ids)) for n, ids in url_ids.items() if len(ids) == 1}
        index.compact_ids = [(_compact(i), i) for i in index.ids.values()]
        return index

    def name_of(self, biotools_id: str) -> str:
        return self.names.get(self.ids.get(biotools_id.lower(), biotools_id), "")

    def _resembles(self, key: str, biotools_id: str) -> bool:
        """Whether a package name looks like the entry it links to: one starts with the other (hmmer, HMMER3),
        or they share a word of at least 4 letters (ltr_finder_parallel, LTR-FINDER-P); not cooler -> scool."""
        for other in (biotools_id, self.names.get(biotools_id, "")):
            a, b = _compact(key), _compact(other)
            if a and b and (a.startswith(b) or b.startswith(a) or _words(key) & _words(other)):
                return True
        return False

    def find(self, key: str) -> tuple[str, str]:
        """(bio.tools ID, method) of a lower-case tool name in the dump, ('', '') if not found."""
        forms = [key] + ([u] if (u := ungrouped(key)) else [])
        for method, table in (
            ("biotools_id", self.ids),
            ("biotools_name", self.by_name),
            ("biotools_url", self.by_url),
        ):
            for form in forms:
                for spelling in spellings(form):
                    found = table.get(spelling)
                    if found and (method != "biotools_url" or self._resembles(form, found)):
                        return found, method
        return "", ""

    def suggest(self, key: str, context: list[str], n: int = 5) -> list[str]:
        """Up to n candidate IDs for an unmapped tool: dump matches of the packages it comes with (context) that
        resemble it, IDs containing the tool name or contained in it, close spellings, and the other context
        matches if there are at most two (a process with bedtools only: genomecoveragebed -> bedtools)."""
        packages = dict.fromkeys(i for p in context if (i := self.find(tool_key(p))[0]))
        found = dict.fromkeys(i for i in packages if self._resembles(key, i))
        key = ungrouped(key) or key
        if len(key) >= MIN_URL_NAME:
            compact = _compact(key)
            containing = sorted((i for c, i in self.compact_ids if compact in c), key=len)
            contained = sorted(
                (i for low, i in self.ids.items() if len(low) >= max(5, len(key) // 2) and low in key),
                key=len,
                reverse=True,
            )
            for biotools_id in itertools.chain(contained[:2], containing[:3]):
                found.setdefault(biotools_id)
            same_start = [low for low in self.ids if low[:1] == key[:1]]
            for low in difflib.get_close_matches(key, same_start, n=3, cutoff=0.8):
                found.setdefault(self.ids[low])
        if len(packages) <= 2:
            for biotools_id in packages:
                found.setdefault(biotools_id)
        return list(found)[:n]


@dataclass(slots=True)
class ToolMap:
    """The bio.tools mapping of one tool node."""

    action: Action
    ids: list[str] = field(default_factory=list)  # several for a curated chain
    method: str = ""  # curated | meta | biotools_id | biotools_name | biotools_url | codex | prefix
    codex_id: str = ""  # the candidates, to spot disagreements
    match_id: str = ""  # the dump match (biotools_id / _name / _url)


@dataclass(slots=True)
class Lookup:
    """Everything a tool name can be mapped with."""

    biotools: BiotoolsIndex
    codex_conda: dict[str, str]  # bioconda package -> bio.tools ID
    codex_name: dict[str, str]  # Galaxy suite ID -> bio.tools ID
    curated: dict[str, CuratedEntry]
    prefix_blocklist: set[str]

    def spelled(self, biotools_id: str) -> str:
        """A bio.tools ID in its real spelling, if known."""
        return self.biotools.ids.get(biotools_id.lower(), biotools_id)

    def _codex(self, key: str) -> str:
        """The Codex ID of a tool name, if it is in bio.tools."""
        for spelling in spellings(key):
            codex_id = self.codex_conda.get(spelling) or self.codex_name.get(spelling, "")
            if codex_id and codex_id.lower() in self.biotools.ids:
                return self.spelled(codex_id)
        return ""

    def map(self, tool: str, source: str, meta_id: str, process: str, declared: str = "") -> ToolMap:
        """Map one tool node; source is how the tool name was found (executable, meta, ..., process),
        declared the tool the module declares for it (bowtie2-build -> bowtie2), tried after the tool itself."""
        curated = self.curated.get(tool.lower()) or self.curated.get(declared.lower())
        if curated:
            return ToolMap(curated.action, [self.spelled(i) for i in curated.ids], "curated")
        keys = [tool_key(tool)] + ([tool_key(declared)] if declared and tool_key(declared) != tool_key(tool) else [])
        match_id, match_method = next((m for k in keys if (m := self.biotools.find(k))[0]), ("", ""))
        codex_id = next((c for k in keys if (c := self._codex(k))), "")
        found = ToolMap("map", codex_id=codex_id, match_id=match_id)
        meta_id = meta_id.removeprefix("biotools:").strip()
        if meta_id and meta_id.lower() in self.biotools.ids:
            found.ids, found.method = [self.spelled(meta_id)], "meta"
        elif match_id:
            found.ids, found.method = [match_id], match_method
        elif codex_id:
            found.ids, found.method = [codex_id], "codex"
        elif source == "process":
            first = process.lower().split("_")[0]
            if first != process.lower() and first not in self.prefix_blocklist and first in self.biotools.ids:
                found.ids, found.method = [self.biotools.ids[first]], "prefix"
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
