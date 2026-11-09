"""
Translates the Galaxy tool pairs from ToolShed names to bio.tools ids.

Step 1: Mapping. For each tool in data/galaxy_tools.csv, try;
  1. codex: the Galaxy Codex tool table, which links ToolShed suites to bio.tools IDs
            (optional: save it as data/galaxy_codex_tools.tsv, see README)
  2. bio.tools ID (name) match:  the ToolShed name is itself a bio.tools ID (e.g. megahit -> megahit), TODO: this might match to random stuff with similar name. check this
            it is also trying '_' and '-' interchangably and without a 'suite_' prefix as it occursoften
  3. by hand: rows in data/manual_map.csv (columns: tool, biotoolsID), which win over 1 and 2
  -> data/galaxy_tool_map.csv
  -> data/unmapped_tools.csv:  tools with no match, to look over later
     it also has the attribute has_publication = the bio.tools entry has a paper, so it can be in the literature graph

Step 2, translating data/galaxy_pairs.csv with created map. 
Pairs where either tool has no bio.tools ID are left out, and pairs where both tools map to the same ID.
ToolShed names are kept as attributes. It outputs;
  -> data/biotools_pairs.csv  one row per workflow and pair
  -> data/biotools_edges.csv  one row per pair, for Cytoscape or the comparison:
  -> data/biotools_nodes.csv  one row per bio.tools id 

Usage (from the repository root, after galaxy_tool_pairs.py):
    .venv/bin/python directed-graph/workflowhub/map_galaxy_tools.py

"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS_FILE = HERE / "data" / "galaxy_tools.csv"
CODEX_FILE = HERE / "data" / "galaxy_codex_tools.tsv"
BIOTOOLS_PUBS = HERE.parent / "biotools" / "data" / "biotools_publications.csv"
# Vedran's full bio.tools dump, under any name starting with biotools_raw
BIOTOOLS_RAW = next(iter(sorted((HERE.parent / "biotools" / "data").glob("biotools_raw*.jsonl"))), None)
MANUAL_FILE = HERE / "data" / "manual_map.csv"
CANDIDATES_FILE = HERE / "data" / "helper_candidates.csv"
OUT_FILE = HERE / "data" / "galaxy_tool_map.csv"
UNMAPPED_FILE = HERE / "data" / "unmapped_tools.csv"
PAIRS_IN = HERE / "data" / "galaxy_pairs.csv"
PAIRS_OUT = HERE / "data" / "biotools_pairs.csv"
EDGES_OUT = HERE / "data" / "biotools_edges.csv"
NODES_OUT = HERE / "data" / "biotools_nodes.csv"


def variants(name):
    """Spellings to try for a ToolShed name."""
    name = name.lower()
    out = {name, name.replace("_", "-"), name.replace("-", "_")}
    if name.startswith("suite_"):
        out |= variants(name[len("suite_"):])
    return out


def find_column(header, *words):
    """First column whose name contains all the words (case-insensitive)."""
    for col in header:
        if all(w in col.lower() for w in words):
            return col
    return None


def load_codex():
    """{(suite, owner) -> biotoolsID} and {suite or tool ID -> biotoolsID} from the Codex table.
    A Codex suite can group several ToolShed repositories, so its 'Tool IDs' are indexed too
    (e.g. tool anndata_manipulate is in suite anndata)."""
    if not CODEX_FILE.exists():
        print(f"No {CODEX_FILE.name}: skipping Codex matching")
        return {}, {}
    csv.field_size_limit(10**9)  # some Codex cells are very long
    with open(CODEX_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        suite_col = find_column(reader.fieldnames, "suite", "id")
        owner_col = find_column(reader.fieldnames, "owner")
        biotools_col = find_column(reader.fieldnames, "bio.tool", "id")
        tool_ids_col = find_column(reader.fieldnames, "tool ids")
        if not suite_col or not biotools_col:
            sys.exit(f"Codex columns not found. Columns are: {reader.fieldnames}")
        print(f"Codex columns used: {suite_col!r}, {owner_col!r}, {biotools_col!r}")
        by_owner, by_name = {}, {}
        for row in reader:
            biotools_id = (row.get(biotools_col) or "").strip()
            suite = (row.get(suite_col) or "").strip().lower()
            if not biotools_id or not suite:
                continue
            owner = (row.get(owner_col) or "").strip().lower() if owner_col else ""
            by_owner[(suite, owner)] = biotools_id
            by_name.setdefault(suite, biotools_id)
            for tool_id in (row.get(tool_ids_col) or "").split(",") if tool_ids_col else []:
                if tool_id.strip():
                    by_name.setdefault(tool_id.strip().lower(), biotools_id)
    return by_owner, by_name


def load_biotools_ids():
    """All bio.tools IDs (lowercase -> real spelling), and the set of those with a paper."""
    with_paper = set()
    with open(BIOTOOLS_PUBS, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            with_paper.add(row["biotoolsID"])
    all_ids = set(with_paper)
    if BIOTOOLS_RAW:  # all of bio.tools, also tools without a paper
        import json
        with open(BIOTOOLS_RAW, encoding="utf-8") as f:
            for line in f:
                all_ids.add(json.loads(line)["biotoolsID"])
    else:
        print("No biotools_raw*.jsonl: name matching only against tools with a paper")
    return {i.lower(): i for i in all_ids}, with_paper


def load_manual():
    """{toolshed name -> biotoolsID} filled in by hand: manual_map.csv and the
    manual_biotoolsID column of helper_candidates.csv, if they exist."""
    manual = {}
    if MANUAL_FILE.exists():
        with open(MANUAL_FILE, encoding="utf-8") as f:
            manual.update({r["tool"].strip(): r["biotoolsID"].strip() for r in csv.DictReader(f) if r.get("biotoolsID")})
    if CANDIDATES_FILE.exists():
        with open(CANDIDATES_FILE, encoding="utf-8") as f:
            manual.update({r["tool"].strip(): r["manual_biotoolsID"].strip()
                           for r in csv.DictReader(f) if (r.get("manual_biotoolsID") or "").strip()})
    return manual


def build_map():
    """Step 1: write galaxy_tool_map.csv and return {(tool, owner) -> biotoolsID}, and the IDs with a paper."""
    codex_by_owner, codex_by_name = load_codex()
    biotools_ids, with_paper = load_biotools_ids()
    manual = load_manual()

    rows = []
    with open(TOOLS_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tool, owner = row["tool"], row["owner"]
            biotools_id, method = "", ""
            key = (tool.lower(), owner.lower())
            codex_id = codex_by_owner.get(key) or codex_by_name.get(tool.lower(), "")
            name_id = next((biotools_ids[v] for v in sorted(variants(tool)) if v in biotools_ids), "")
            prefix = tool.lower().split("_")[0]
            prefix_id = biotools_ids.get(prefix, "") if prefix != tool.lower() else ""
            if tool in manual:
                biotools_id, method = manual[tool], "hand"
            elif codex_id:
                biotools_id, method = codex_id, "codex"
            elif name_id:
                biotools_id, method = name_id, "name"
            elif prefix_id:
                biotools_id, method = prefix_id, "prefix"
            disagree = bool(codex_id and name_id and codex_id.lower() != name_id.lower())
            rows.append({**row, "biotoolsID": biotools_id, "method": method,
                         "codex_id": codex_id, "name_id": name_id, "disagree": str(disagree).lower(),
                         "has_publication": str(biotools_id in with_paper).lower()})

    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    total = sum(int(r["n_workflows"]) for r in rows)
    mapped = [r for r in rows if r["biotoolsID"]]
    methods = ", ".join(f"{m} {sum(r['method'] == m for r in rows)}" for m in ("hand", "codex", "name", "prefix"))
    print(f"Tools: {len(rows)}, mapped: {len(mapped)} ({methods}), "
          f"with a paper: {sum(r['has_publication'] == 'true' for r in rows)}")
    print(f"Tool uses covered: {sum(int(r['n_workflows']) for r in mapped)}/{total}")
    print("Most used unmapped tools (add to manual_map.csv, or to HELPERS):")
    for r in [r for r in rows if not r["biotoolsID"]][:15]:
        print(f"  {r['n_workflows']:>5}  {r['tool']} ({r['owner']})")
    unmapped = [r for r in rows if not r["biotoolsID"]]
    with open(UNMAPPED_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["tool", "owner", "n_workflows"], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(unmapped)
    print(f"Codex and name match disagree: {sum(r['disagree'] == 'true' for r in rows)}")
    print(f"Wrote {OUT_FILE.name}, {UNMAPPED_FILE.name} ({len(unmapped)} tools)")
    return {(r["tool"], r["owner"]): r["biotoolsID"] for r in mapped}, with_paper


def translate(tool_map, with_paper):
    """Step 2: rewrite galaxy_pairs.csv with bio.tools IDs, keeping the ToolShed names as attributes."""
    pair_rows = []
    edge_workflows = defaultdict(set)            # (source, target) -> workflow IDs
    edge_toolshed = defaultdict(lambda: (set(), set()))  # (source, target) -> ToolShed names on each side
    node_workflows = defaultdict(set)            # biotoolsID -> workflow IDs
    node_toolshed = defaultdict(set)             # biotoolsID -> ToolShed names
    n_in = n_unmapped = n_same = 0

    with open(PAIRS_IN, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            n_in += 1
            src = tool_map.get((row["source"], row["source_owner"]))
            tgt = tool_map.get((row["target"], row["target_owner"]))
            if not src or not tgt:
                n_unmapped += 1
                continue
            if src == tgt:
                n_same += 1
                continue
            wf = row["workflow_id"]
            pair_rows.append([wf, src, tgt, row["source"], row["target"]])
            edge_workflows[(src, tgt)].add(wf)
            edge_toolshed[(src, tgt)][0].add(row["source"])
            edge_toolshed[(src, tgt)][1].add(row["target"])
            for bt, ts in ((src, row["source"]), (tgt, row["target"])):
                node_workflows[bt].add(wf)
                node_toolshed[bt].add(ts)

    # one row per workflow and pair (a workflow can give the same pair from two .ga files or names)
    pair_rows = sorted({tuple(r) for r in pair_rows}, key=lambda r: (int(r[0]), r[1], r[2]))
    with open(PAIRS_OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["workflow_id", "source", "target", "source_toolshed", "target_toolshed"])
        writer.writerows(pair_rows)

    with open(EDGES_OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "target", "n_workflows", "workflow_ids", "source_toolshed", "target_toolshed"])
        for (src, tgt), ids in sorted(edge_workflows.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            ts_src, ts_tgt = edge_toolshed[(src, tgt)]
            writer.writerow([src, tgt, len(ids), ";".join(sorted(ids, key=int)),
                             ";".join(sorted(ts_src)), ";".join(sorted(ts_tgt))])

    with open(NODES_OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["biotoolsID", "toolshed_names", "n_workflows", "has_publication"])
        for bt, ids in sorted(node_workflows.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            writer.writerow([bt, ";".join(sorted(node_toolshed[bt])), len(ids), str(bt in with_paper).lower()])

    print(f"Pairs: {n_in} in, {n_unmapped} left out (a tool without bio.tools ID), "
          f"{n_same} left out (both sides the same bio.tools ID)")
    print(f"Wrote {PAIRS_OUT.name} ({len(pair_rows)} rows), {EDGES_OUT.name} ({len(edge_workflows)} edges), "
          f"{NODES_OUT.name} ({len(node_workflows)} nodes)")


def main():
    tool_map, with_paper = build_map()
    translate(tool_map, with_paper)


if __name__ == "__main__":
    main()