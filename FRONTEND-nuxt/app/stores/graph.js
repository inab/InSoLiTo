export const useGraphStore = defineStore('graph', () => {
    // Each node/edge keeps the full `properties` object from Neo4j (not just
    // the fields the UI happens to render today), so future features don't
    // require redesigning the store.
    const nodes = ref([])
    const edges = ref([])

    function setGraph (newNodes, newEdges) {
        nodes.value = newNodes
        edges.value = newEdges
    }

    // Merges a search result into the existing graph instead of replacing it,
    // matching the old app's additive behaviour (searching a second tool adds
    // its neighbours rather than starting over). Dedupes by Neo4j's node/edge id.
    function addToGraph (newNodes, newEdges) {
        const existingNodeIds = new Set(nodes.value.map((node) => node.id))
        const existingEdgeIds = new Set(edges.value.map((edge) => edge.id))
        nodes.value = [...nodes.value, ...newNodes.filter((node) => !existingNodeIds.has(node.id))]
        edges.value = [...edges.value, ...newEdges.filter((edge) => !existingEdgeIds.has(edge.id))]
    }

    function reset () {
        nodes.value = []
        edges.value = []
    }

    return { nodes, edges, setGraph, addToGraph, reset }
})
