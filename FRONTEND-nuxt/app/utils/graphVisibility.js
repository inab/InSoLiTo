// A node is hidden if its type is in hiddenTypes OR its community is in
// hiddenCommunities OR (Tool/Database only) none of its toolType values are still
// active — all three rule sets apply at once regardless of which legend tab (By
// type / By topic) you're currently looking at, so toggling a layer in one view
// stays applied when you switch to the other. Entry-point nodes (the tool/database
// actually searched for, not just a neighbour) are always exempt — they should never
// disappear behind a layer filter.
//
// toolType is an array (a tool can be both 'cmd' and 'web') — "any active" rather
// than "any hidden" semantics, so unchecking one category only hides nodes that are
// EXCLUSIVELY that category, not every node that happens to also carry it.
export function isNodeHidden (node, { hiddenTypes, hiddenCommunities, hiddenToolTypes = [], entryPointIds = [] }) {
    if (entryPointIds.includes(node.id)) return false
    if (hiddenTypes.includes(node.type) || hiddenCommunities.includes(node.properties?.community)) return true
    const toolType = node.properties?.toolType
    if (toolType?.length && hiddenToolTypes.length) {
        return toolType.every((type) => hiddenToolTypes.includes(type))
    }
    return false
}

// Drops hidden nodes and any edge touching one — used for the JSON export so the file
// matches what's actually on screen. The PNG export gets this for free (Cytoscape
// simply doesn't draw display:none elements), but the JSON is built straight from
// graphStore, which has no notion of "currently hidden".
export function filterVisibleGraph (nodes, edges, visibility) {
    const visibleNodes = nodes.filter((node) => !isNodeHidden(node, visibility))
    const visibleIds = new Set(visibleNodes.map((node) => node.id))
    const visibleEdges = edges.filter((edge) => visibleIds.has(edge.source) && visibleIds.has(edge.target))
    return { nodes: visibleNodes, edges: visibleEdges }
}
