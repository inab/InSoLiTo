"""
Extract the process DAG of each downloaded Nextflow workflow, by reading its .nf files (nothing is run).

Input:  data/download/nextflow/<id>_v<version>/      (from download_workflowhub_nextflow.py)
Output: data/nextflow/<id>_v<version>/nodes.csv     one row per process node, with all tool information
        data/nextflow/<id>_v<version>/edges.csv     source, target, channel
        data/nextflow/<id>_v<version>/warnings.log  what could not be resolved
        data/nextflow/nextflow_dags.csv             one row per workflow: counts and warnings
The bio.tools mapping of these DAGs is in mapping.py (map_nextflow_tools.py).

Step 1 (read):    all .nf files; comments removed, strings masked so braces in scripts do not count  (groovy.py)
Step 2 (process): sections, directives and script of every process, and its tool information
                  (executables, containers, conda packages, versions.yml tools, nf-core meta.yml)
                                                                          (sources.py, process.py, shell.py)
Step 3 (graph):   DSL1: channels named in `from` / `into`, linked through top-level `.into{}`, `.set{}`, `x = ...`
                  DSL2: the entry workflow, with subworkflows inlined and named like Nextflow (`SUB:PROC`).
                  Every if/else branch is taken, so the DAG is the union over all parameter choices.
                                                                          (build.py, dsl1.py, dsl2.py)

This is static analysis of Groovy code, so it is heuristic: unusual code can lose edges.
Names that could not be resolved are listed in warnings.log.

Usage (from the repository root):
    python3 directed-graph/workflowhub/extract_nextflow_dags.py
    python3 directed-graph/workflowhub/extract_nextflow_dags.py --only 462_v3 --verbose
or, from directed-graph/workflowhub/:
    python3 -m nfdag --only 462_v3 --verbose
"""

from .build import Result, build

__all__ = ["Result", "build"]
