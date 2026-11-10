"""Extract EDAM topics and operations per tool from the raw bio.tools dump.

Writes one row per tool. List-valued columns use "|" as the separator and
every field is quoted.

Usage:
    python extract_topics_operations.py [input.jsonl] [output.csv]
"""

import csv
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def edam_id(uri):
    return uri.rsplit("/", 1)[-1] if uri else ""


def unique(items):
    """Drop duplicates and empty values, keeping the first-seen order."""
    seen = set()
    out = []
    for x in items:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def main():
    if len(sys.argv) > 1:
        src = sys.argv[1]
    else:
        src = sorted(glob.glob(os.path.join(DATA, "biotools_raw*.jsonl")))[-1]
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(DATA, "biotools_topics_operations.csv")

    header = [
        "biotoolsID", "name",
        "n topics", "topics", "topic ids",
        "n operations", "operations", "operation ids",
    ]
    n = 0
    with open(src) as fin, open(dst, "w", newline="") as fout:
        w = csv.writer(fout, quoting=csv.QUOTE_ALL)
        w.writerow(header)
        for line in fin:
            r = json.loads(line)
            topics = r.get("topic") or []
            ops = [op for f in (r.get("function") or []) for op in (f.get("operation") or [])]

            topic_ids = unique(edam_id(t.get("uri")) for t in topics)
            topic_terms = unique(t.get("term") for t in topics)
            op_ids = unique(edam_id(o.get("uri")) for o in ops)
            op_terms = unique(o.get("term") for o in ops)

            w.writerow([
                r.get("biotoolsID", ""), r.get("name", ""),
                len(topic_ids), "|".join(topic_terms), "|".join(topic_ids),
                len(op_ids), "|".join(op_terms), "|".join(op_ids),
            ])
            n += 1
    print(f"Wrote {n} tools to {dst}")


if __name__ == "__main__":
    main()
