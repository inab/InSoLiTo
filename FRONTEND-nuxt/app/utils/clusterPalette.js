// Deterministic pseudo-random hash: same seed always maps to the same value in
// [0, 1). Classic sin-based hash (same trick used for GLSL noise) — not for
// security, just a stable, well-distributed number from an arbitrary seed.
function hashToUnitInterval (seed) {
    const x = Math.sin(seed) * 43758.5453
    return x - Math.floor(x)
}

// A community's color depends only on its id — the same id always renders the same
// color, in the legend, on the canvas, or in the node info panel, regardless of what
// else is in the graph at the time. Hue/saturation/lightness use different multipliers
// so the three don't move together, reducing (though not eliminating) the chance that
// two arbitrary ids happen to look alike side by side.
function communityColor (id) {
    const hue = Math.floor(hashToUnitInterval(id * 12.9898) * 360)
    const saturation = 42 + Math.floor(hashToUnitInterval(id * 78.233) * 18) // 42-60%
    const lightness = 44 + Math.floor(hashToUnitInterval(id * 39.346) * 16) // 44-60%
    // No spaces after the commas: Network.vue joins two of these into one
    // "line-gradient-stop-colors" value ("<bg1> <bg2>"), a Cytoscape multi-value
    // property split on whitespace — an internal space here would break that split
    // and throw deep inside Cytoscape's style parser (crashing its render loop).
    return {
        bg: `hsl(${hue},${saturation}%,${lightness}%)`,
        border: `hsl(${hue},${saturation + 4}%,${Math.max(lightness - 20, 22)}%)`
    }
}

// community id -> { bg, border } CSS color strings, one entry per distinct community
// present in `nodes`.
export function buildClusterColorMap (nodes) {
    const colorMap = {}
    nodes.forEach((node) => {
        const id = node.properties?.community
        if (id === undefined || id === null || colorMap[id]) return
        colorMap[id] = communityColor(id)
    })
    return colorMap
}

// Single-id variant for callers that only need one community's color (e.g. the node
// info panel), without building a map over the whole graph.
export function getCommunityColor (id) {
    return communityColor(id)
}
