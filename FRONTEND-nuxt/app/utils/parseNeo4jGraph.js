// Converts a Neo4j HTTP transactional endpoint response (resultDataContents: ['graph'])
// into the { nodes, edges } shape graphStore expects. Dedupes by Neo4j's own internal
// id, same as the old app's idNodesSet/idEdgesSet, since a search can return nodes/edges
// already present in the graph.
export function parseNeo4jGraph (response) {
    const nodesById = new Map()
    const edgesById = new Map()

    for (const row of response.results[0].data) {
        for (const node of row.graph.nodes) {
            if (nodesById.has(node.id)) continue
            const type = node.labels[0]
            const label = type === 'Publication' ? node.properties.subtitle : node.properties.name
            nodesById.set(node.id, { id: node.id, label, type, properties: node.properties })
        }
        for (const rel of row.graph.relationships) {
            if (edgesById.has(rel.id)) continue
            edgesById.set(rel.id, {
                id: rel.id,
                source: rel.startNode,
                target: rel.endNode,
                weight: rel.properties.times,
                properties: rel.properties
            })
        }
    }

    return { nodes: [...nodesById.values()], edges: [...edgesById.values()] }
}
