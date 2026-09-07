import { communityMetaById } from './communityTopics'
import { formatToolType } from './toolTypeLabels'

function triggerDownload (href, filename) {
    const link = document.createElement('a')
    link.href = href
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
}

function downloadBlob (content, type, filename) {
    const blob = new Blob([content], { type })
    const url = URL.createObjectURL(blob)
    triggerDownload(url, filename)
    URL.revokeObjectURL(url)
}

export function downloadDataUri (dataUri, filename) {
    triggerDownload(dataUri, filename)
}

// "InSoLiTo-graph.json" for every export made it hard to tell files apart once
// you'd exported more than one search — this names the file after what was
// actually searched instead. Truncated (not just capped, so it never cuts a
// term's name in half) so a long list of active searches doesn't produce an
// unusably long filename; falls back to the generic name for an empty list
// (shouldn't happen in practice, Export only shows once there's a graph).
export function graphExportFilename (searchTerms, extension) {
    const MAX_LENGTH = 60
    const slug = searchTerms
        .map((term) => term.name.replace(/[^a-zA-Z0-9]+/g, '-').replace(/^-+|-+$/g, ''))
        .filter(Boolean)
        .reduce((acc, part) => {
            if (!acc.length) return [part]
            const next = [...acc, part].join('-')
            return next.length <= MAX_LENGTH ? [...acc, part] : acc
        }, [])
        .join('-')
    return `InSoLiTo-${slug || 'graph'}.${extension}`
}

// metadata (searchTerms, filters) is what makes the file re-importable (see
// utils/graphState.js) — this is the only format this app reads back in. CSV
// carries the same metadata too, but only as an informational key,value table
// (see downloadGraphAsCsv below); GraphML stays data-only, since neither format
// is a reimport contract, just a convenience for opening in Excel/Gephi/Cytoscape
// Desktop.
export function downloadGraphAsJson (nodes, edges, metadata) {
    // Metadata first, same header-before-data ordering as the CSV's ## METADATA
    // section — object key order doesn't affect parsing, only how it reads.
    const payload = { ...metadata, nodes, edges }
    downloadBlob(JSON.stringify(payload, null, 2), 'application/json', graphExportFilename(metadata.searchTerms, 'json'))
}

function csvField (value) {
    return `"${String(value ?? '').replace(/"/g, '""')}"`
}

// Three sections in one file — same ## NODES / ## EDGES shape the old FRONTEND/
// (webpack) app's exportCSV() used (graph.js), with a ## METADATA section added
// ahead of it. Informational only here (unlike the JSON export, this file is never
// read back into the app — CSV is for opening in Excel/spreadsheets), so it's a
// plain key,value table rather than the structured searchTerms/filters object.
export function downloadGraphAsCsv (nodes, edges, metadata) {
    const metaRows = [
        ['version', metadata.version],
        ['exported_at', metadata.exportedAt],
        ['search_terms', metadata.searchTerms.map((term) => `${term.name} (${term.kind})`).join('; ')],
        ['year_min', metadata.filters.yearMin ?? ''],
        ['year_max', metadata.filters.yearMax ?? ''],
        ['occurrence_min', metadata.filters.occurrenceMin ?? '']
    ].map((row) => row.map(csvField).join(',')).join('\n')
    const nodeRows = nodes
        .map((node) => {
            const community = node.properties?.community
            const meta = community !== undefined && community !== null ? communityMetaById[community] : null
            const toolType = (node.properties?.toolType ?? []).map(formatToolType).join('; ')
            return [
                node.id, node.label, node.type, community ?? '', node.properties?.topiclabel ?? '',
                toolType, meta?.Language ?? '', meta?.OS ?? ''
            ].map(csvField).join(',')
        })
        .join('\n')
    const edgeRows = edges
        .map((edge) => [edge.source, edge.target, edge.weight ?? ''].map(csvField).join(','))
        .join('\n')
    const csv =
        `## METADATA\nkey,value\n${metaRows}\n\n` +
        `## NODES\nid,label,type,community,topic,tool_type,community_language,community_os\n${nodeRows}\n\n` +
        `## EDGES\nsource,target,co_citations\n${edgeRows}\n`
    downloadBlob(csv, 'text/csv;charset=utf-8;', graphExportFilename(metadata.searchTerms, 'csv'))
}

function xmlEscape (value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
}

// Standard GraphML (opens directly in Gephi/Cytoscape Desktop) — <key> elements
// declare the attribute schema once, <data> elements reference them by id per
// GraphML's own convention. searchTerms is only for the filename (see
// graphExportFilename) — the file's actual content stays data-only, same
// reasoning as downloadGraphAsCsv's doc comment above.
export function downloadGraphAsGraphml (nodes, edges, searchTerms) {
    const nodeXml = nodes.map((node) => (
        `    <node id="n${xmlEscape(node.id)}">\n` +
        `      <data key="label">${xmlEscape(node.label)}</data>\n` +
        `      <data key="type">${xmlEscape(node.type)}</data>\n` +
        `      <data key="community">${xmlEscape(node.properties?.community ?? '')}</data>\n` +
        '    </node>'
    )).join('\n')
    const edgeXml = edges.map((edge) => (
        `    <edge source="n${xmlEscape(edge.source)}" target="n${xmlEscape(edge.target)}">\n` +
        `      <data key="weight">${xmlEscape(edge.weight ?? '')}</data>\n` +
        '    </edge>'
    )).join('\n')

    const graphml =
        '<?xml version="1.0" encoding="UTF-8"?>\n' +
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n' +
        '  <key id="label" for="node" attr.name="label" attr.type="string"/>\n' +
        '  <key id="type" for="node" attr.name="type" attr.type="string"/>\n' +
        '  <key id="community" for="node" attr.name="community" attr.type="string"/>\n' +
        '  <key id="weight" for="edge" attr.name="weight" attr.type="double"/>\n' +
        '  <graph id="InSoLiTo" edgedefault="undirected">\n' +
        `${nodeXml}\n${edgeXml}\n` +
        '  </graph>\n' +
        '</graphml>\n'
    downloadBlob(graphml, 'application/xml', graphExportFilename(searchTerms, 'graphml'))
}
