"""
Extract tool order in the Galaxy workflows downloaded by download_workflowhub.py.

Reads data/download/workflows.csv and the .ga files in data/download/ga/, and writes:
  - data/galaxy/galaxy_pairs.csv  one row per workflow and tool pair: tool A feeds tool B
  - data/galaxy/galaxy_edges.csv  one row per tool pair, summed over workflows
  - data/galaxy/galaxy_tools.csv  one row per tool, and how many workflows use it

Tools are named by their ToolShed repository (e.g. "megahit"), not yet by bio.tools ID.
Steps that are not real tools (inputs, Galaxy built-ins such as __APPLY_RULES__, and the
helper tools in HELPERS) are skipped, and the real tools on each side are connected through
them.

Subworkflows are read as separate graphs: pairs inside them are kept, but pairs that cross
the subworkflow boundary are not (yet).

Usage (from repo root, after download_workflowhub.py):
    .venv/bin/python directed-graph/workflowhub/galaxy_tool_pairs.py
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
WORKFLOWS_FILE = DATA_DIR / "download" / "workflows.csv"
GA_DIR = DATA_DIR / "download" / "ga"
OUT_DIR = DATA_DIR / "galaxy"
PAIRS_FILE = OUT_DIR / "galaxy_pairs.csv"
EDGES_FILE = OUT_DIR / "galaxy_edges.csv"
TOOLS_FILE = OUT_DIR / "galaxy_tools.csv"

# ToolShed repositories that move or reshape data rather than analyse it.
# TODO: There may be more of these - expand if so
HELPERS = {
    "text_processing", "collection_element_identifiers", "map_param_value",
    "pick_value", "param_value_from_file",
    "collapse_collections", "column_maker", "regex_find_replace",
    "compose_text_param", "datamash_ops", "query_tabular",
    "split_file_to_collection", "anndata_inspect",
}


def tool_of(step):
    """(repository name, owner) for a real ToolShed tool, else None."""
    if step.get("type") != "tool":
        return None
    repo = step.get("tool_shed_repository")
    if not repo or repo.get("name") in HELPERS:
        return None
    return repo["name"], repo.get("owner", "")


def connections(step):
    """IDs of the steps this step reads from. A connection can be one dict or a list of them."""
    ids = set()
    for value in (step.get("input_connections") or {}).values():
        for conn in value if isinstance(value, list) else [value]:
            if isinstance(conn, dict) and "id" in conn:
                ids.add(int(conn["id"]))
    return ids


def pairs_in(workflow):
    """Set of ((tool, owner), (tool, owner)) pairs in one Galaxy workflow dict, subworkflows included."""
    steps = {int(k): v for k, v in (workflow.get("steps") or {}).items()}
    parents = {i: connections(s) for i, s in steps.items()}

    def nearest_tools(i, seen):
        """Closest upstream real tools, walking through skipped steps."""
        found = set()
        for p in parents.get(i, ()):
            if p in seen or p not in steps:
                continue
            seen.add(p)
            if tool_of(steps[p]):
                found.add(p)
            else:
                found |= nearest_tools(p, seen)
        return found

    pairs = set()
    for i, step in steps.items():
        if tool_of(step):
            for p in nearest_tools(i, set()):
                if tool_of(steps[p]) != tool_of(step):  # ignore a tool feeding itself
                    pairs.add((tool_of(steps[p]), tool_of(step)))
        if step.get("type") == "subworkflow" and isinstance(step.get("subworkflow"), dict):
            pairs |= pairs_in(step["subworkflow"])
    return pairs


def tools_in(workflow):
    """Set of (tool, owner) in one Galaxy workflow dict, subworkflows included."""
    tools = set()
    for step in (workflow.get("steps") or {}).values():
        if tool_of(step):
            tools.add(tool_of(step))
        if step.get("type") == "subworkflow" and isinstance(step.get("subworkflow"), dict):
            tools |= tools_in(step["subworkflow"])
    return tools


def main():
    if not WORKFLOWS_FILE.exists():
        sys.exit(f"{WORKFLOWS_FILE} not found - run download_workflowhub.py first")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pair_rows = []
    edge_workflows = defaultdict(set)
    tool_workflows = defaultdict(set)
    n_workflows = n_unreadable = 0

    with open(WORKFLOWS_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["workflow_class"].lower() != "galaxy" or not row["ga_files"]:
                continue
            n_workflows += 1
            wf_id, version = row["id"], row["version"]
            for ga_name in row["ga_files"].split(";"):
                path = GA_DIR / f"{wf_id}_v{version}" / ga_name
                try:
                    workflow = json.loads(path.read_text(encoding="utf-8-sig"))
                except (OSError, json.JSONDecodeError) as error:
                    print(f"  skip {path}: {error}", file=sys.stderr)
                    n_unreadable += 1
                    continue
                for tool in tools_in(workflow):
                    tool_workflows[tool].add(wf_id)
                for (src, src_owner), (tgt, tgt_owner) in sorted(pairs_in(workflow)):
                    pair_rows.append([wf_id, version, ga_name, src, tgt, src_owner, tgt_owner])
                    edge_workflows[(src, tgt)].add(wf_id)

    with open(PAIRS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["workflow_id", "version", "ga_file", "source", "target", "source_owner", "target_owner"])
        writer.writerows(pair_rows)

    with open(EDGES_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "target", "n_workflows", "workflow_ids"])
        for (src, tgt), ids in sorted(edge_workflows.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            writer.writerow([src, tgt, len(ids), ";".join(sorted(ids, key=int))])

    with open(TOOLS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["tool", "owner", "n_workflows"])
        for (tool, owner), ids in sorted(tool_workflows.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            writer.writerow([tool, owner, len(ids)])

    print(f"Galaxy workflows read: {n_workflows} ({n_unreadable} .ga files unreadable)")
    print(f"Pairs: {len(pair_rows)} rows -> {PAIRS_FILE.name}")
    print(f"Distinct directed edges: {len(edge_workflows)} -> {EDGES_FILE.name}")
    print(f"Distinct tools: {len(tool_workflows)} -> {TOOLS_FILE.name}")
    print("Most used tools (check for helper tools to add to HELPERS):")
    for (tool, owner), ids in sorted(tool_workflows.items(), key=lambda kv: -len(kv[1]))[:15]:
        print(f"  {len(ids):5d}  {tool} ({owner})")


if __name__ == "__main__":
    main()