"""Extract the process DAG of each downloaded Nextflow workflow. The code is in the nfdag package next to this file.

Usage (from the repository root):
    python3 directed-graph/workflowhub/extract_nextflow_dags.py
    python3 directed-graph/workflowhub/extract_nextflow_dags.py --only 462_v3 --verbose
"""

from nfdag.cli import main

if __name__ == "__main__":
    main()
