"""Convert the OEB Observatory tools JSON to the format of the old OEB snapshot.

The pipeline (InferToolsKeywords.py, CalculateCitations.py) reads the tools in
the format of the old OEB API (monitor/rest/search?=publications). This script
writes the Observatory tools in that same format, so the pipeline does not
change: only OEB_JSON in run_pipeline.sh points to the new file.

Decisions (2026-11-05):
  - Only entries with a bio.tools ID (a 'biotools/<id>/...' item in source).
  - An entry with several bio.tools IDs gives one tool per ID, each with all
    the publications of the entry (data as they are). Its name is the ID, so
    that two tools do not share the same name.
  - Entries with the same bio.tools ID are merged into one tool.
  - One output entry per tool and type, as in the old snapshot (@type is a
    single string there). The type 'undefined' is left out.
  - Publications with no PMID and no DOI are left out.
  - No languages (the Observatory has none).

Run from BH2026-InSoLiTo/:
    .venv/bin/python DB/pipeline/convert_observatory.py
"""

import json
import re
from collections import Counter

INPUT = 'DB/raw_data/observatory/tools.json'
OUTPUT = 'DB/raw_data/observatory/tools_oeb_format.json'

# EDAM URIs the pipeline can look up in the ontology (others are left out).
EDAM_URI = re.compile(r'^http://edamontology\.org/(topic|operation|data|format)_\d+$')

with open(INPUT, encoding='utf-8') as f:
    entries = json.load(f)['message']['tools']

counts = Counter()
left_out_uris = Counter()  # EDAM URIs left out, to check that the filter is right


def edam(uri):
    """The URI if it is a valid EDAM URI, otherwise None (and counted)."""
    if isinstance(uri, str) and EDAM_URI.match(uri):
        return uri
    if uri:
        counts['edam_uris_left_out'] += 1
        # Grouped by the start of the URI (up to the last '/')
        left_out_uris[str(uri).rsplit('/', 1)[0][:80]] += 1
    return None


def as_list(value):
    return value if isinstance(value, list) else []


# One record per bio.tools ID, merging the entries that share it.
tools = {}
for entry in entries:
    data = entry['data']
    ids = sorted({s.split('/')[1] for s in entry['source'] if s.startswith('biotools/')})
    if not ids:
        counts['entries_without_biotools_id'] += 1
        continue
    if len(ids) > 1:
        counts['entries_with_several_ids'] += 1

    for biotools_id in ids:
        name = data['name'] if len(ids) == 1 else biotools_id
        if biotools_id in tools:
            counts['entries_merged'] += 1
            tool = tools[biotools_id]
            if tool['name'] != name:
                counts['merged_with_different_name'] += 1
        else:
            tool = tools[biotools_id] = {
                'name': name, 'types': set(), 'os': set(), 'publications': {},
                'topics': set(), 'operations': set(), 'inputs': {}, 'outputs': {},
            }

        tool['types'].update(t for t in as_list(data.get('type')) if t and t != 'undefined')
        tool['os'].update(o for o in as_list(data.get('operating_system')) + as_list(data.get('operating_systems'))
                          if isinstance(o, str) and o)

        for pub in as_list(data.get('publication')) + as_list(data.get('publications')):
            if not isinstance(pub, dict):
                continue
            pmid = str(pub.get('pmid') or '').strip()
            doi = (pub.get('doi') or '').strip()
            new = {}
            if pmid.isdigit():
                new['pmid'] = pmid
            if doi:
                new['doi'] = doi
            if not new:
                counts['publications_without_pmid_or_doi'] += 1
                continue
            # Same paper listed twice: keep it once
            tool['publications'][(new.get('pmid'), new.get('doi'))] = new

        for field, target in (('topics', 'topics'), ('operations', 'operations')):
            for term in as_list(data.get(field)):
                uri = edam(term.get('uri')) if isinstance(term, dict) else None
                if uri:
                    tool[target].add(uri)

        # input/output: 'uri' is the format, 'datatype.uri' the type of data.
        # Old format: {"datatype": <uri>, "formats": [<uri>, ...]} per data type.
        for field, target in (('input', 'inputs'), ('output', 'outputs')):
            for term in as_list(data.get(field)):
                if not isinstance(term, dict):
                    continue
                datatype = term.get('datatype') or {}
                datatype_uri = edam(datatype.get('uri')) if isinstance(datatype, dict) else None
                format_uri = edam(term.get('uri'))
                if not datatype_uri and not format_uri:
                    continue
                item = tool[target].setdefault(datatype_uri, set())
                if format_uri:
                    item.add(format_uri)


def semantics(tool):
    def in_out(groups):
        result = []
        for datatype, formats in groups.items():
            item = {'formats': sorted(formats)}
            if datatype:
                item['datatype'] = datatype
            result.append(item)
        return result
    return {
        'topics': sorted(tool['topics']),
        'operations': sorted(tool['operations']),
        'inputs': in_out(tool['inputs']),
        'outputs': in_out(tool['outputs']),
    }


# Old format: one entry per tool and type (a tool with no type: one entry, @type None).
output = []
for biotools_id, tool in sorted(tools.items()):
    base = {
        '@label': biotools_id,
        'name': tool['name'],
        'os': sorted(tool['os']),
        'publications': list(tool['publications'].values()),
        'semantics': semantics(tool),
    }
    for tool_type in sorted(tool['types']) or [None]:
        output.append({'@type': tool_type, **base})

with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False)

with_pmid = sum(1 for t in tools.values() if any('pmid' in p for p in t['publications'].values()))
with_pub = sum(1 for t in tools.values() if t['publications'])
print(f'Observatory entries: {len(entries)}')
for name, count in sorted(counts.items()):
    print(f'  {name}: {count}')
print(f'Tools (one per bio.tools ID): {len(tools)}')
print(f'  with at least one publication: {with_pub}')
print(f'  with at least one PMID: {with_pmid}')
print(f'  with type db: {sum(1 for t in tools.values() if "db" in t["types"])}')
print(f'Output entries (one per tool and type): {len(output)}')
print(f'Written {OUTPUT}')
print(f'\nMost common EDAM URIs left out ({len(left_out_uris)} different):')
for uri, count in left_out_uris.most_common(20):
    print(f'  {count}: {uri!r}')
