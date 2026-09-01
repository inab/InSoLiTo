import ToolTopicData from '../../../DB/ToolTopicAutocomplete.json'

// Landing-page stats, computed once from the same bundled JSON the autocomplete
// already uses — no Neo4j query involved, consistent with the rest of the app's
// "4 static JSONs, live queries only on search" runtime model (see CLAUDE.md).
// Deduped by name+kind, same reasoning as toolTopicLookup.js's suggestSearchTerms:
// the dataset has same-tool duplicates across separate OEB registrations (e.g.
// "Anchor"/"ANCHOR"), which would otherwise inflate the counts.
export function datasetStats () {
    const seen = new Set()
    const counts = { Tool: 0, Database: 0, Topic: 0 }

    for (const entry of ToolTopicData) {
        if (typeof entry.value !== 'string') continue
        const kind = Array.isArray(entry.labelnode) ? entry.labelnode[0] : entry.labelnode
        if (!(kind in counts)) continue
        const key = `${entry.value.toLowerCase()}|${kind}`
        if (seen.has(key)) continue
        seen.add(key)
        counts[kind]++
    }

    return {
        toolCount: counts.Tool,
        databaseCount: counts.Database,
        topicCount: counts.Topic
    }
}
