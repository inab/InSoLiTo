// Query shape mirrors the Cypher variants documented in CLAUDE.md (Tool/Database
// search vs Topic search, each with/without a year filter). Publications are
// fetched like any other neighbour — the "By type" legend (uiStore.hiddenTypes)
// is what lets a user hide them, same as Tool/Database. Values are always sent as
// query parameters, not string-concatenated, so a search term can never break
// out of the Cypher statement.
const OCCURRENCE_MAX = 100

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
                `WHERE m.times>=$cMin AND m.times<=$cMax${yearClause} ` +
                'RETURN nt1,m,nt2',
            parameters
        }
    }

    // Tool/Database search, matched by exact node name.
    const yearClause = hasYearFilter ? ' AND o.year>=$yMin AND o.year<=$yMax' : ''
    return {
        statement:
            `MATCH (i)-[o:${relType}]-(p) ` +
            `WHERE i.name=$name AND o.times>=$cMin AND o.times<=$cMax${yearClause} ` +
            'RETURN i,o,p ORDER BY o.times',
        parameters
    }
}
