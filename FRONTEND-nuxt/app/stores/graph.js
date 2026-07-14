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

    function reset () {
        nodes.value = []
        edges.value = []
    }

    return { nodes, edges, setGraph, reset }
})
