export const useGraphStore = defineStore('graph', () => {
    // Each node/edge keeps the full `properties` object from Neo4j (not just
    // the fields the UI happens to render today), so future features don't
    // require redesigning the store.
    const nodes = ref([])
    const edges = ref([])
    // ids of nodes that were an actual search target (not just pulled in as a
    // neighbour) — accumulates across searches, same additive spirit as nodes/edges.
    const entryPointIds = ref([])
    // { name, kind } pairs remembered across searches so the whole graph can be
    // rebuilt from scratch (e.g. when filters change, or one entry is removed)
    // instead of only ever growing. Cleared only by reset(), not by clearResults().
    const searchTerms = ref([])

    function addSearchTerm (term) {
        const exists = searchTerms.value.some((t) => t.name === term.name && t.kind === term.kind)
        if (!exists) searchTerms.value = [...searchTerms.value, term]
    }

    function removeSearchTerm (term) {
        searchTerms.value = searchTerms.value.filter((t) => !(t.name === term.name && t.kind === term.kind))
    }

    // Merges a search result into the existing graph instead of replacing it,
    // matching the old app's additive behaviour (searching a second tool adds
    // its neighbours rather than starting over). Dedupes by Neo4j's node/edge id.
    // entryPointId is tracked separately from the dedup above: a node already in the
    // graph as someone else's neighbour can later become an entry point in its own
    // right, and that has to register even though the node object itself isn't "new".
    function addToGraph (newNodes, newEdges, entryPointId) {
        const existingNodeIds = new Set(nodes.value.map((node) => node.id))
        const existingEdgeIds = new Set(edges.value.map((edge) => edge.id))
        nodes.value = [...nodes.value, ...newNodes.filter((node) => !existingNodeIds.has(node.id))]
        edges.value = [...edges.value, ...newEdges.filter((edge) => !existingEdgeIds.has(edge.id))]
        if (entryPointId !== undefined && entryPointId !== null && !entryPointIds.value.includes(entryPointId)) {
            entryPointIds.value = [...entryPointIds.value, entryPointId]
        }
    }

    // Empties the graph but keeps searchTerms — used before rebuilding from the
    // remembered search terms (filter change, or removing one entry) so the terms
    // that drive the rebuild survive the clear.
    function clearResults () {
        nodes.value = []
        edges.value = []
        entryPointIds.value = []
    }

    function reset () {
        clearResults()
        searchTerms.value = []
    }

    return { nodes, edges, entryPointIds, searchTerms, addSearchTerm, removeSearchTerm, addToGraph, clearResults, reset }
})
