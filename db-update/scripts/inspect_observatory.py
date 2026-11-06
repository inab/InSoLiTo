"""Look at the structure of the OEB Observatory tools JSON (read only).

Prints how the file is organised, how many entries it has, which fields the
entries have (and in how many entries each one appears) and the first entry
in full, so we can see whether it has what the pipeline needs (bio.tools ID,
PMID/DOI of the publications, type, languages, OS, EDAM terms).

Run from BH2026-InSoLiTo/:
    db-update/.venv/bin/python db-update/scripts/inspect_observatory.py
"""

import json
from collections import Counter

INPUT = 'db-update/raw_data/observatory/tools.json'
MAX_CHARS = 6000  # cut the printed entry so it does not flood the terminal

with open(INPUT, encoding='utf-8') as f:
    data = json.load(f)

# Find the list of tools: go down through the objects, printing each level,
# until reaching a list (the biggest one at each level).
def describe(value):
    if isinstance(value, (list, dict)):
        return f'{type(value).__name__} with {len(value)} items'
    return f'{type(value).__name__}: {str(value)[:200]!r}'

node, path = data, 'file'
while isinstance(node, dict):
    print(f'{path}:')
    for key, value in node.items():
        print(f'  key {key!r}: {describe(value)}')
    containers = [(k, v) for k, v in node.items() if isinstance(v, (list, dict))]
    if not containers:
        break
    key, node = max(containers, key=lambda kv: len(json.dumps(kv[1])))
    path = f'{path}[{key!r}]'
entries = node if isinstance(node, list) else []
print(f'\nList of entries found at: {path}')

print(f'\nEntries: {len(entries)}')

# Fields of the entries and how many entries have each one.
fields = Counter()
for entry in entries:
    if isinstance(entry, dict):
        fields.update(entry.keys())
print('\nFields (number of entries that have them):')
for name, count in fields.most_common():
    print(f'  {name}: {count}')

# First entry in full (cut at MAX_CHARS).
if entries:
    text = json.dumps(entries[0], indent=2, ensure_ascii=False)
    print(f'\nFirst entry ({len(text)} characters):')
    print(text[:MAX_CHARS])
    if len(text) > MAX_CHARS:
        print('... (cut)')

# Fields inside 'data' that are not empty, and in how many entries.
def has_content(value):
    return value not in (None, '', [], {}, False)

filled = Counter()
with_biotools_source = 0
for entry in entries:
    for name, value in entry.get('data', {}).items():
        if has_content(value):
            filled[name] += 1
    if any(s.startswith('biotools/') for s in entry.get('source', [])):
        with_biotools_source += 1
print(f'\nFields of data with content (out of {len(entries)} entries):')
for name, count in filled.most_common():
    print(f'  {name}: {count}')
print(f'\nEntries with a biotools/... item in source: {with_biotools_source}')

# One entry with publications and one with sources_labels, to see their shape.
for field in ('publication', 'citation', 'sources_labels'):
    example = next((e for e in entries if has_content(e['data'].get(field))), None)
    if example:
        text = json.dumps(example['data'][field], indent=2, ensure_ascii=False)
        print(f'\nExample of {field} (tool {example["data"].get("name")!r}, source {example["source"]}):')
        print(text[:MAX_CHARS])

# Publications: how many tools have at least one PMID, or only a DOI.
def publications(entry):
    data = entry['data']
    return (data.get('publication') or []) + (data.get('publications') or [])

with_pmid = only_doi = 0
for entry in entries:
    pubs = [p for p in publications(entry) if isinstance(p, dict)]
    if any(p.get('pmid') for p in pubs):
        with_pmid += 1
    elif any(p.get('doi') for p in pubs):
        only_doi += 1
print(f'\nTools with at least one PMID: {with_pmid}')
print(f'Tools with a DOI but no PMID: {only_doi}')

# bio.tools IDs: the second part of each 'biotools/<id>/...' item in source.
ids_per_entry = Counter()
entries_per_id = Counter()
for entry in entries:
    ids = {s.split('/')[1] for s in entry['source'] if s.startswith('biotools/')}
    ids_per_entry[len(ids)] += 1
    entries_per_id.update(ids)
print('\nEntries by number of different bio.tools IDs in source:')
for n, count in sorted(ids_per_entry.items()):
    print(f'  {n}: {count}')
repeated = [(i, n) for i, n in entries_per_id.most_common() if n > 1]
print(f'bio.tools IDs that appear in more than one entry: {len(repeated)}')
print(f'  first ones: {repeated[:10]}')

# Real examples of the two cases: one entry with several bio.tools IDs, and
# one bio.tools ID in several entries. For each entry: name, bio.tools IDs,
# and DOI or PMID of its publications.
def summary(entry):
    ids = sorted({s.split('/')[1] for s in entry['source'] if s.startswith('biotools/')})
    pubs = [p.get('doi') or p.get('pmid') for p in publications(entry) if isinstance(p, dict)]
    return f'name {entry["data"].get("name")!r}, bio.tools IDs {ids}, publications {pubs}'

print('\nExamples: one entry with several bio.tools IDs')
several = [e for e in entries
           if len({s.split('/')[1] for s in e['source'] if s.startswith('biotools/')}) >= 2]
for entry in several[:4]:
    print(f'  {summary(entry)}')

print('\nExamples: one bio.tools ID in several entries')
for biotools_id, _ in repeated[:4]:
    print(f'  ID {biotools_id!r}:')
    for entry in entries:
        if any(s.startswith(f'biotools/{biotools_id}/') for s in entry['source']):
            print(f'    {summary(entry)}')

# Values of type.
types = Counter(t for e in entries for t in (e['data'].get('type') or []))
print(f'\nValues of type: {types.most_common()}')

# Shape of input and output.
for field in ('input', 'output'):
    example = next((e for e in entries if has_content(e['data'].get(field))), None)
    if example:
        text = json.dumps(example['data'][field], indent=2, ensure_ascii=False)
        print(f'\nExample of {field} (tool {example["data"].get("name")!r}):')
        print(text[:2000])
