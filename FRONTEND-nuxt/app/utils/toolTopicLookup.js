import ToolTopicData from '../../../DB/ToolTopicAutocomplete.json'

// Resolves free-typed search text to a known tool/topic name and its kind, by
// exact (case-insensitive) match against the bundled autocomplete dataset. This
// also doubles as the search's only validation: text that isn't in the dataset
// never reaches the Cypher query.
export function resolveSearchTerm (rawTerm) {
    const term = rawTerm.trim().toLowerCase()
    if (!term) return null

    const match = ToolTopicData.find((entry) => entry.value.toLowerCase() === term)
    if (!match) return null

    const kind = Array.isArray(match.labelnode) ? match.labelnode[0] : match.labelnode
    return { name: match.value, kind }
}

// Suggestions for the search box as the user types: prefix matches first, then
// "contains" matches, same two-pass order as the old jQuery UI autocomplete.
export function suggestSearchTerms (rawTerm, limit = 8) {
    const term = rawTerm.trim().toLowerCase()
    if (!term) return []

    const startsWith = []
    const contains = []
    const seen = new Set()

    for (const entry of ToolTopicData) {
        if (typeof entry.value !== 'string') continue
        const value = entry.value.toLowerCase()
        // Same name in different casing (e.g. "Anchor"/"ANCHOR") happens across
        // separate OEB registrations of the same tool — dedupe on name+kind, not the
        // raw string, so they don't show up as two near-identical suggestions.
        const kind = Array.isArray(entry.labelnode) ? entry.labelnode[0] : entry.labelnode
        const dedupeKey = `${value}|${kind}`
        if (seen.has(dedupeKey)) continue
        if (value.startsWith(term)) {
            startsWith.push(entry)
            seen.add(dedupeKey)
        } else if (value.includes(term)) {
            contains.push(entry)
            seen.add(dedupeKey)
        }
    }

    return [...startsWith, ...contains].slice(0, limit).map((entry) => ({
        name: entry.value,
        kind: Array.isArray(entry.labelnode) ? entry.labelnode[0] : entry.labelnode
    }))
}
