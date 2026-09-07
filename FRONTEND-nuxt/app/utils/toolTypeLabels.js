// toolType[] (see CLAUDE.md, Neo4j field audit 2026-09-02) is 100% populated on
// every Tool/Database node but stores short OpenEBench codes, not display text.
// Only the values actually seen in production are named here — anything else
// (a future OEB type this map hasn't been updated for) falls back to a
// capitalized version of the raw code, so a new type never renders as blank.
const TOOL_TYPE_LABELS = {
    cmd: 'Command line',
    web: 'Web service',
    lib: 'Library',
    db: 'Database',
    app: 'Desktop application',
    soap: 'SOAP',
    suite: 'Suite',
    rest: 'REST API',
    script: 'Script',
    workflow: 'Workflow',
    plugin: 'Plugin',
    workbench: 'Workbench',
    ontology: 'Ontology',
    sparql: 'SPARQL endpoint'
}

export function formatToolType (type) {
    return TOOL_TYPE_LABELS[type] || (type.charAt(0).toUpperCase() + type.slice(1))
}
