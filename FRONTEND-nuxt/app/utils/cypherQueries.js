import OccurData from '../../../DB/RelationshipSliderData.json'

// Query shape mirrors the Cypher variants documented in CLAUDE.md (Tool/Database
// search vs Topic search, each with/without a year filter). Publications are
// fetched like any other neighbour — the "By type" legend (uiStore.hiddenTypes)
// is what lets a user hide them, same as Tool/Database. Values are always sent as
// query parameters, not string-concatenated, so a search term can never break
// out of the Cypher statement.
// cMax must match the occurrence slider's real domain max (Sidebar.vue derives the
// same value from this JSON) — a hardcoded ceiling below the real data max would
// make any occurrenceMin above it return zero rows regardless of what exists.
const OCCURRENCE_MAX = Math.max(...Object.keys(OccurData).map(Number))

export function buildSearchQuery ({ name, kind, occurrenceMin, yearMin, yearMax }) {
    const hasYearFilter = yearMin != null && yearMax != null
    const relType = hasYearFilter ? 'METAOCCUR' : 'METAOCCUR_ALL'
    const parameters = { name, cMin: occurrenceMin ?? 0, cMax: OCCURRENCE_MAX }
    if (hasYearFilter) {
        parameters.yMin = yearMin
        parameters.yMax = yearMax
    }

    if (kind === 'Topic') {
        const yearClause = hasYearFilter ? ' AND m.year>=$yMin AND m.year<=$yMax' : ''
        return {
            statement:
                'MATCH (n)-[:TOPIC]->(k:Keyword)-[:SUBCLASS*]->(k2:Keyword) ' +
                'WHERE k2.label=$name OR k.label=$name ' +
                'WITH DISTINCT n WITH collect(n) AS nt UNWIND nt AS nt1 UNWIND nt AS nt2 ' +
                `MATCH (nt1)-[m:${relType}]-(nt2) ` +
                // id(nt1)<>id(nt2): excludes a tool co-cited with its own other publication
                // (self-loop) — not a distinct-tool relationship, no signal for this graph.
                `WHERE id(nt1)<>id(nt2) AND m.times>=$cMin AND m.times<=$cMax${yearClause} ` +
                'RETURN nt1,m,nt2',
            parameters
        }
    }

    // Tool/Database search, matched by exact node name.
    const yearClause = hasYearFilter ? ' AND o.year>=$yMin AND o.year<=$yMax' : ''
    return {
        statement:
            `MATCH (i)-[o:${relType}]-(p) ` +
            // id(i)<>id(p): same self-loop exclusion as the Topic branch above.
            `WHERE i.name=$name AND id(i)<>id(p) AND o.times>=$cMin AND o.times<=$cMax${yearClause} ` +
            'RETURN i,o,p ORDER BY o.times',
        parameters
    }
}

// One-off query for a single edge already on screen (default graph query stays on
// METAOCCUR_ALL, the per-year detail is fetched only on demand). Matched by Neo4j's
// internal node id rather than name — the endpoints are already known nodes, not a
// fresh search term, and a Publication node has no `name` to match on anyway.
export function buildEdgeYearBreakdownQuery ({ sourceId, targetId }) {
    return {
        statement:
            'MATCH (a)-[r:METAOCCUR]-(b) WHERE id(a)=$aId AND id(b)=$bId ' +
            'RETURN r.year AS year, r.times AS times ORDER BY r.year',
        parameters: { aId: Number(sourceId), bId: Number(targetId) }
    }
}
