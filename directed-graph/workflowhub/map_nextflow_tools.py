"""
Translates the Nextflow DAGs (tool nodes) to bio.tools IDs, like map_galaxy_tools.py does for Galaxy.

Reads data/nextflow/<id>_v<version>/{nodes,edges}.csv (from extract_nextflow_dags.py) and the hand-curated
nextflow_curated_map.tsv next to this script. The mapping methods are described in nfdag/mapping.py:
curated > meta (nf-core meta.yml) > codex (Galaxy Codex, also by bioconda package) > name > prefix.

It outputs:
  - data/mapping/nextflow/nextflow_tool_map.tsv   one row per tool name, with the ID and the method used
  - data/mapping/nextflow/nextflow_to_curate.tsv  tools without ID, mapped only by prefix, or where codex and
                                                  name disagree, most used first. The first four columns are
                                                  those of the curated TSV: fill in action (map/drop) and
                                                  biotoolsID, and copy the row into nextflow_curated_map.tsv
  - data/biotools/nextflow/biotools_pairs.csv     one row per workflow and pair
  - data/biotools/nextflow/biotools_edges.csv     one row per pair, summed over workflows
  - data/biotools/nextflow/biotools_nodes.csv     one row per bio.tools ID
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
    CODEX_FILE,
    MAPPING,
    PREFIX_BLOCKLIST,
    find_column,
    load_biotools_ids,
    variants,
)
from nfdag.mapping import CURATED_FIELDS, BiotoolsPair, Lookup, ToolMap, read_curated, translate

HERE = Path(__file__).resolve().parent
DAG_DIR = HERE / "data" / "nextflow"
CURATED_FILE = HERE / "nextflow_curated_map.tsv"
MAP_DIR = MAPPING / "nextflow"
OUT_DIR = BIOTOOLS_DIR / "nextflow"
EXAMPLES = 3  # example processes / workflows per tool in the TSVs


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


def write_tool_map(tools: dict[str, ToolStats], with_paper: set[str]) -> None:
    columns = [
        "tool",
        "biotoolsID",
        "method",
        "codex_id",
        "name_id",
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
                    s.mapping.method,
                    s.mapping.codex_id,
                    s.mapping.name_id,
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


def write_to_curate(tools: dict[str, ToolStats]) -> int:
    """Tools a person should look at; the first columns are those of the curated TSV."""
    rows = []
    for tool, s in tools.items():
        m = s.mapping
        disagree = bool(m.codex_id and m.name_id and m.codex_id.lower() != m.name_id.lower())
        if m.method == "curated" or not (m.action == "unmapped" or m.method == "prefix" or disagree):
            continue
        reason = (
            "unmapped"
            if m.action == "unmapped"
            else "prefix match"
            if m.method == "prefix"
            else (f"codex {m.codex_id} vs name {m.name_id}")
        )
        guess = ";".join(m.ids) or m.codex_id or m.name_id
        rows.append(
            (
                s,
                [
                    tool,
                    "",
                    guess,
                    reason,
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
            [*CURATED_FIELDS, "n_workflows", "n_nodes", "lost_edges", "processes", "modules", "containers", "conda"]
        )
        writer.writerows(r for _, r in rows)
    return len(rows)


def write_biotools(pairs: dict[str, list[BiotoolsPair]], with_paper: set[str]) -> None:
    """The bio.tools pairs per workflow, summed edges and nodes, and one CSV per workflow."""
    workflows_dir = OUT_DIR / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    edge_workflows: dict[tuple[str, str], set[str]] = defaultdict(set)
    edge_tools: dict[tuple[str, str], tuple[set[str], set[str]]] = defaultdict(lambda: (set(), set()))
    node_workflows: dict[str, set[str]] = defaultdict(set)
    node_tools: dict[str, set[str]] = defaultdict(set)
    with (OUT_DIR / "biotools_pairs.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["workflow_id", "version", "source", "target", "kind", "source_node", "target_node"])
        for name, workflow_pairs in pairs.items():
            workflow_id, version = name.split("_v")
            unique = sorted({(p.source, p.target, p.kind, p.source_node, p.target_node) for p in workflow_pairs})
            writer.writerows([workflow_id, version, *p] for p in unique)
            with (workflows_dir / f"{name}.csv").open("w", newline="", encoding="utf-8") as wf:
                per_workflow = csv.writer(wf)
                per_workflow.writerow(["source", "target", "kind", "source_node", "target_node"])
                per_workflow.writerows(unique)
            for source, target, _, source_node, target_node in unique:
                edge_workflows[(source, target)].add(workflow_id)
                edge_tools[(source, target)][0].add(source_node.rsplit("/", 1)[-1])
                edge_tools[(source, target)][1].add(target_node.rsplit("/", 1)[-1])
                for biotools_id, node in ((source, source_node), (target, target_node)):
                    node_workflows[biotools_id].add(workflow_id)
                    node_tools[biotools_id].add(node.rsplit("/", 1)[-1])
    with (OUT_DIR / "biotools_edges.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "target", "n_workflows", "workflow_ids", "source_tools", "target_tools"])
        for (source, target), ids in sorted(edge_workflows.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            src_tools, tgt_tools = edge_tools[(source, target)]
            writer.writerow(
                [
                    source,
                    target,
                    len(ids),
                    ";".join(sorted(ids, key=int)),
                    ";".join(sorted(src_tools)),
                    ";".join(sorted(tgt_tools)),
                ]
            )
    with (OUT_DIR / "biotools_nodes.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["biotoolsID", "tools", "n_workflows", "has_publication"])
        for biotools_id, ids in sorted(node_workflows.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            writer.writerow(
                [
                    biotools_id,
                    ";".join(sorted(node_tools[biotools_id])),
                    len(ids),
                    str(biotools_id in with_paper).lower(),
                ]
            )
    print(
        f"Wrote {OUT_DIR}: {sum(len(p) for p in pairs.values())} pairs, {len(edge_workflows)} edges, "
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

    biotools_ids, with_paper = load_biotools_ids()
    print(f"Codex: {CODEX_FILE}" if CODEX_FILE.exists() else f"No {CODEX_FILE.name}: skipping Codex matching")
    codex_name = load_codex_suites()
    curated = read_curated(args.curated)
    unknown = sorted({i for e in curated.values() for i in e.ids if i.lower() not in biotools_ids})
    if unknown:
        print(f"Curated IDs not found in bio.tools (check spelling): {', '.join(unknown)}")
    lookup = Lookup(biotools_ids, load_codex_conda(), codex_name, curated, variants, PREFIX_BLOCKLIST)

    tools, pairs = map_workflows(lookup, args.dags)
    write_tool_map(tools, with_paper)
    n_curate = write_to_curate(tools)

    nodes = sum(s.nodes for s in tools.values())
    print(f"Tool names: {len(tools)}, tool nodes: {nodes}")
    for method in ("curated", "meta", "codex", "name", "prefix"):
        chosen = [s for s in tools.values() if s.mapping.method == method]
        print(f"  {method:8s} {len(chosen):5d} tools, {sum(s.nodes for s in chosen):6d} nodes")
    for action in ("drop", "unmapped"):
        chosen = [s for s in tools.values() if s.mapping.action == action]
        print(f"  {action:8s} {len(chosen):5d} tools, {sum(s.nodes for s in chosen):6d} nodes")
    unmapped = sorted((s for s in tools.values() if s.mapping.action == "unmapped"), key=lambda s: -len(s.workflows))
    print(f"DAG edges lost at unmapped tools: {sum(s.lost_edges for s in tools.values())}")
    print(f"Wrote {MAP_DIR / 'nextflow_to_curate.tsv'} ({n_curate} tools). Most used unmapped:")
    for s in unmapped[:15]:
        tool = next(t for t, v in tools.items() if v is s)
        print(f"  {len(s.workflows):5d}  {tool}  ({_examples(s.processes)})")
    write_biotools(pairs, with_paper)


if __name__ == "__main__":
    main()
