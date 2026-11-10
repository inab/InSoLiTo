"""
Translates the Nextflow DAGs (tool nodes) to bio.tools IDs, like map_galaxy_tools.py does for Galaxy.

Reads data/nextflow/<id>_v<version>/{nodes,edges}.csv (from extract_nextflow_dags.py) and the hand-curated
nextflow_curated_map.tsv next to this script. The reference is the bio.tools dump
(directed-graph/biotools/data/biotools_raw*.jsonl). The mapping methods are described in nfdag/mapping.py:
curated > meta (nf-core meta.yml) > biotools_id > biotools_name > biotools_url > codex (Galaxy Codex) > prefix.

It outputs:
  - data/mapping/nextflow/nextflow_tool_map.tsv   one row per tool name, with the ID and the method used
  - data/mapping/nextflow/nextflow_to_curate.tsv  tools without ID or mapped only by prefix, most used first,
                                                  with suggestions. The first four columns are those of the
                                                  curated TSV: fill in action (map/drop) and biotoolsID, and
                                                  copy the row into nextflow_curated_map.tsv
  - data/biotools/nextflow/biotools_pairs.csv     one row per workflow and pair       } the same columns as the
  - data/biotools/nextflow/biotools_edges.csv     one row per pair, over workflows    } Galaxy files, with bio.tools
  - data/biotools/nextflow/biotools_nodes.csv     one row per bio.tools ID            } names for ToolShed names
  - data/biotools/nextflow/workflows/<id>_v<version>.csv   the bio.tools DAG of each workflow (for Cytoscape)

Usage (from the repository root, after extract_nextflow_dags.py):
    python3 directed-graph/workflowhub/map_nextflow_tools.py
"""

import argparse
import csv
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from map_galaxy_tools import (
    BIOTOOLS_DIR,
    BIOTOOLS_PUBS,
    BIOTOOLS_RAW,
    CODEX_FILE,
    MAPPING,
    PREFIX_BLOCKLIST,
    find_column,
    variants,
)
from nfdag.mapping import (
    CURATED_FIELDS,
    BiotoolsIndex,
    BiotoolsPair,
    Lookup,
    ToolMap,
    read_curated,
    tool_key,
    translate,
)

HERE = Path(__file__).resolve().parent
DAG_DIR = HERE / "data" / "nextflow"
CURATED_FILE = HERE / "nextflow_curated_map.tsv"
MAP_DIR = MAPPING / "nextflow"
OUT_DIR = BIOTOOLS_DIR / "nextflow"
EXAMPLES = 3  # example processes / workflows per tool in the TSVs
METHODS = ("curated", "meta", "biotools_id", "biotools_name", "biotools_url", "codex", "prefix")


def load_codex_suites() -> dict[str, str]:
    """{Galaxy suite ID -> bio.tools ID}. Unlike map_galaxy_tools.load_codex, without the tool IDs inside a
    suite: those are Galaxy wrapper names (the srst2 suite has a tool `samtools`), not executables."""
    if not CODEX_FILE.exists():
        return {}
    csv.field_size_limit(10**9)
    with CODEX_FILE.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        suite_col = find_column(reader.fieldnames, "suite", "id")
        biotools_col = find_column(reader.fieldnames, "bio.tool", "id")
        if not suite_col or not biotools_col:
            return {}
        out: dict[str, str] = {}
        for row in reader:
            suite, biotools_id = (row.get(suite_col) or "").strip().lower(), (row.get(biotools_col) or "").strip()
            if suite and biotools_id:
                for name in variants(suite):
                    out.setdefault(name, biotools_id)
    return out


def load_with_paper() -> set[str]:
    """The bio.tools IDs with a publication."""
    with BIOTOOLS_PUBS.open(encoding="utf-8") as f:
        return {row["biotoolsID"] for row in csv.DictReader(f)}


def _name_parts(name: str) -> set[str]:
    return {p for p in re.split(r"[-_.]", name.lower()) if len(p) > 2}


def load_codex_conda() -> dict[str, str]:
    """{bioconda package -> bio.tools ID} from the Codex column 'Suite conda package'.
    That is the main requirement of a Galaxy suite, often only a dependency (a suite needing samtools is about
    srst2, one needing pandas about image analysis). So per package the most common bio.tools ID of its suites
    is taken, and only if it or one of those suites shares a name part with the package
    (samtools -> samtools, ncbi-amrfinderplus -> amrfinderplus, pandas -> nothing)."""
    if not CODEX_FILE.exists():
        return {}
    csv.field_size_limit(10**9)
    with CODEX_FILE.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        conda_col = "Suite conda package" if "Suite conda package" in (reader.fieldnames or []) else None
        suite_col = find_column(reader.fieldnames, "suite", "id")
        biotools_col = find_column(reader.fieldnames, "bio.tool", "id")
        if not conda_col or not suite_col or not biotools_col:
            return {}
        suites: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))  # package -> ID -> suites
        for row in reader:
            biotools_id = (row.get(biotools_col) or "").strip()
            suite = (row.get(suite_col) or "").strip()
            for package in (row.get(conda_col) or "").split(",") if biotools_id else []:
                if package.strip():
                    suites[package.strip().lower()][biotools_id].append(suite)
    out = {}
    for package, by_id in suites.items():
        biotools_id, its_suites = max(by_id.items(), key=lambda kv: len(kv[1]))
        names = _name_parts(biotools_id).union(*(_name_parts(s) for s in its_suites))
        if _name_parts(package) & names:
            out[package] = biotools_id
    return out


@dataclass
class ToolStats:
    """What is known about one tool name over all workflows."""

    mapping: ToolMap
    workflows: set[str] = field(default_factory=set)
    nodes: int = 0
    lost_edges: int = 0
    processes: dict[str, None] = field(default_factory=dict)  # ordered set
    modules: dict[str, None] = field(default_factory=dict)
    containers: dict[str, None] = field(default_factory=dict)
    conda: dict[str, None] = field(default_factory=dict)


def _examples(values: dict[str, None]) -> str:
    return ";".join(v for v in list(values)[:EXAMPLES] if v)


def _workflow_dirs(dag_dir: Path) -> list[Path]:
    dirs = [p for p in dag_dir.iterdir() if (p / "nodes.csv").is_file()]
    return sorted(dirs, key=lambda p: int(p.name.split("_")[0]))


def map_workflows(lookup: Lookup, dag_dir: Path) -> tuple[dict[str, ToolStats], dict[str, list[BiotoolsPair]]]:
    """Map all tool nodes; returns per tool name its statistics, and per workflow its bio.tools pairs."""
    tools: dict[str, ToolStats] = {}
    pairs: dict[str, list[BiotoolsPair]] = {}
    for folder in _workflow_dirs(dag_dir):
        with (folder / "nodes.csv").open(encoding="utf-8") as f:
            nodes = list(csv.DictReader(f))
        with (folder / "edges.csv").open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if "kind" not in (reader.fieldnames or []) or (nodes and "tool" not in nodes[0]):
                sys.exit(f"{folder} holds process-level DAGs from an older version: run extract_nextflow_dags.py again")
            edges = [(e["source"], e["target"], e["kind"]) for e in reader]
        mapped: dict[str, ToolMap] = {}
        tool_of = {r["node"]: r["tool"].lower() for r in nodes}
        for row in nodes:
            m = lookup.map(
                row["tool"], row["tool_source"], row["meta_biotools_id"], row["process"], row["declared_tool"]
            )
            mapped[row["node"]] = m
            stats = tools.setdefault(row["tool"].lower(), ToolStats(m))
            if stats.mapping.action == "unmapped" and m.action != "unmapped":  # mapped here (e.g. by meta.yml)
                stats.mapping = m
            stats.workflows.add(folder.name)
            stats.nodes += 1
            for target, value in ((stats.processes, row["process"]), (stats.modules, row["module"])):
                target.setdefault(value)
            for container in row["containers"].split(";")[:1]:
                stats.containers.setdefault(container)
            stats.conda.setdefault(row["conda_packages"])
        pairs[folder.name], _ = translate(mapped, edges)
        for a, b, _ in edges:  # the edges each unmapped tool cuts, to rank the curation
            for node in (a, b):
                if mapped[node].action == "unmapped":
                    tools[tool_of[node]].lost_edges += 1
    return tools, pairs


def _names(index: BiotoolsIndex, ids: list[str]) -> str:
    return ";".join(index.name_of(i) for i in ids)


def write_tool_map(tools: dict[str, ToolStats], index: BiotoolsIndex, with_paper: set[str]) -> None:
    columns = [
        "tool",
        "biotoolsID",
        "biotools_name",
        "method",
        "codex_biotoolsID",
        "match_biotoolsID",
        "n_workflows",
        "n_nodes",
        "lost_edges",
        "processes",
        "modules",
        "containers",
        "conda",
        "has_publication",
    ]
    with (MAP_DIR / "nextflow_tool_map.tsv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(columns)
        for tool, s in sorted(tools.items(), key=lambda kv: (-len(kv[1].workflows), kv[0])):
            ids = ";".join(s.mapping.ids) if s.mapping.action == "map" else s.mapping.action
            writer.writerow(
                [
                    tool,
                    ids,
                    _names(index, s.mapping.ids),
                    s.mapping.method,
                    s.mapping.codex_id,
                    s.mapping.match_id,
                    len(s.workflows),
                    s.nodes,
                    s.lost_edges,
                    _examples(s.processes),
                    _examples(s.modules),
                    _examples(s.containers),
                    _examples(s.conda),
                    str(any(i in with_paper for i in s.mapping.ids)).lower(),
                ]
            )


def _context(s: ToolStats) -> list[str]:
    """Package names the tool comes with: conda packages and container tools (bioconda::bedtools=2.31 -> bedtools)."""
    names = []
    for value in [*s.conda, *s.containers]:
        for item in value.split(";"):
            name = item.rsplit("::", 1)[-1].rsplit("/", 1)[-1]
            name = re.split(r"[=:<>]", name)[0].strip()
            if name and name not in names and not name.startswith(("sha256", "data")):
                names.append(name)
    return names


def write_to_curate(tools: dict[str, ToolStats], index: BiotoolsIndex) -> int:
    """Tools a person should look at (unmapped, or only a prefix match of the process name);
    the first columns are those of the curated TSV."""
    rows = []
    for tool, s in tools.items():
        m = s.mapping
        if m.action != "unmapped" and m.method != "prefix":
            continue
        reason = "unmapped" if m.action == "unmapped" else "prefix match"
        guess = ";".join(m.ids)
        suggestions = index.suggest(tool_key(tool), _context(s)) if m.action == "unmapped" else []
        rows.append(
            (
                s,
                [
                    tool,
                    "",
                    guess,
                    reason,
                    "; ".join(f"{i} ({index.name_of(i)})" for i in suggestions),
                    _names(index, m.ids),
                    m.codex_id,
                    m.match_id,
                    len(s.workflows),
                    s.nodes,
                    s.lost_edges,
                    _examples(s.processes),
                    _examples(s.modules),
                    _examples(s.containers),
                    _examples(s.conda),
                ],
            )
        )
    rows.sort(key=lambda r: (-len(r[0].workflows), -r[0].lost_edges, r[1][0]))
    with (MAP_DIR / "nextflow_to_curate.tsv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(
            [
                *CURATED_FIELDS,
                "suggestions",
                "biotools_name",
                "codex_biotoolsID",
                "match_biotoolsID",
                "n_workflows",
                "n_nodes",
                "lost_edges",
                "processes",
                "modules",
                "containers",
                "conda",
            ]
        )
        writer.writerows(r for _, r in rows)
    return len(rows)


def write_biotools(pairs: dict[str, list[BiotoolsPair]], index: BiotoolsIndex, with_paper: set[str]) -> None:
    """The same three files as map_galaxy_tools.py, with the bio.tools names in place of the ToolShed names,
    and one CSV per workflow."""
    workflows_dir = OUT_DIR / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    edge_workflows: dict[tuple[str, str], set[str]] = defaultdict(set)
    node_workflows: dict[str, set[str]] = defaultdict(set)
    n_pairs = 0
    with (OUT_DIR / "biotools_pairs.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["workflow_id", "source", "target", "source_biotools_name", "target_biotools_name"])
        for name, workflow_pairs in pairs.items():
            workflow_id = name.split("_v")[0]
            unique = sorted({(p.source, p.target, p.kind, p.source_node, p.target_node) for p in workflow_pairs})
            with (workflows_dir / f"{name}.csv").open("w", newline="", encoding="utf-8") as wf:
                per_workflow = csv.writer(wf)
                per_workflow.writerow(["source", "target", "kind", "source_node", "target_node"])
                per_workflow.writerows(unique)
            for source, target in sorted({(p[0], p[1]) for p in unique}):  # like Galaxy: once per workflow
                writer.writerow([workflow_id, source, target, index.name_of(source), index.name_of(target)])
                n_pairs += 1
                edge_workflows[(source, target)].add(workflow_id)
                node_workflows[source].add(workflow_id)
                node_workflows[target].add(workflow_id)
    with (OUT_DIR / "biotools_edges.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["source", "target", "n_workflows", "workflow_ids", "source_biotools_name", "target_biotools_name"]
        )
        for (source, target), ids in sorted(edge_workflows.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            writer.writerow(
                [
                    source,
                    target,
                    len(ids),
                    ";".join(sorted(ids, key=int)),
                    index.name_of(source),
                    index.name_of(target),
                ]
            )
    with (OUT_DIR / "biotools_nodes.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["biotoolsID", "biotools_name", "n_workflows", "has_publication"])
        for biotools_id, ids in sorted(node_workflows.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            writer.writerow([biotools_id, index.name_of(biotools_id), len(ids), str(biotools_id in with_paper).lower()])
    print(
        f"Wrote {OUT_DIR}: {n_pairs} pairs, {len(edge_workflows)} edges, "
        f"{len(node_workflows)} bio.tools nodes, {len(pairs)} workflow CSVs"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dags", type=Path, default=DAG_DIR, help="the DAGs (default: data/nextflow)")
    parser.add_argument("--curated", type=Path, default=CURATED_FILE, help="the curated TSV")
    args = parser.parse_args()
    if not args.dags.is_dir():
        sys.exit(f"{args.dags} not found - run extract_nextflow_dags.py first")
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if BIOTOOLS_RAW is None:
        sys.exit("No bio.tools dump (directed-graph/biotools/data/biotools_raw*.jsonl): it is the mapping reference")
    print(f"bio.tools: {BIOTOOLS_RAW}")
    index = BiotoolsIndex.load(BIOTOOLS_RAW)
    with_paper = load_with_paper()
    print(f"Codex: {CODEX_FILE}" if CODEX_FILE.exists() else f"No {CODEX_FILE.name}: skipping Codex matching")
    curated = read_curated(args.curated)
    unknown = sorted({i for e in curated.values() for i in e.ids if i.lower() not in index.ids})
    if unknown:
        print(f"Curated IDs not found in bio.tools (check spelling): {', '.join(unknown)}")
    lookup = Lookup(index, load_codex_conda(), load_codex_suites(), curated, PREFIX_BLOCKLIST)

    tools, pairs = map_workflows(lookup, args.dags)
    write_tool_map(tools, index, with_paper)
    n_curate = write_to_curate(tools, index)

    nodes = sum(s.nodes for s in tools.values())
    print(f"Tool names: {len(tools)}, tool nodes: {nodes}")
    for method in METHODS:
        chosen = [s for s in tools.values() if s.mapping.method == method]
        print(f"  {method:13s} {len(chosen):5d} tools, {sum(s.nodes for s in chosen):6d} nodes")
    for action in ("drop", "unmapped"):
        chosen = [s for s in tools.values() if s.mapping.action == action]
        print(f"  {action:13s} {len(chosen):5d} tools, {sum(s.nodes for s in chosen):6d} nodes")
    kept = sum(s.nodes for s in tools.values() if s.mapping.action != "drop")
    mapped = sum(s.nodes for s in tools.values() if s.mapping.action == "map")
    print(f"Coverage: {mapped} of {kept} tool nodes not dropped are bio.tools entries ({mapped / max(kept, 1):.1%})")
    unmapped = sorted((s for s in tools.values() if s.mapping.action == "unmapped"), key=lambda s: -len(s.workflows))
    print(f"DAG edges lost at unmapped tools: {sum(s.lost_edges for s in tools.values())}")
    print(f"Wrote {MAP_DIR / 'nextflow_to_curate.tsv'} ({n_curate} tools). Most used unmapped:")
    for s in unmapped[:15]:
        tool = next(t for t, v in tools.items() if v is s)
        print(f"  {len(s.workflows):5d}  {tool}  ({_examples(s.processes)})")
    write_biotools(pairs, index, with_paper)


if __name__ == "__main__":
    main()
