<template>
  <div ref="containerEl" class="graph-network" />
</template>

<script setup>
import cytoscape from 'cytoscape'
import fcose from 'cytoscape-fcose'

cytoscape.use(fcose)

const props = defineProps({
    // [{ id, label, type: 'Tool' | 'Database' | 'Publication', properties }]
    nodes: { type: Array, default: () => [] },
    // [{ id, source, target, weight, properties }]
    edges: { type: Array, default: () => [] },
    // 'type' colors by Tool/Database/Publication; 'topic' colors by Louvain community.
    colorMode: { type: String, default: 'type' },
    hiddenTypes: { type: Array, default: () => [] },
    hiddenCommunities: { type: Array, default: () => [] },
    hiddenToolTypes: { type: Array, default: () => [] },
    // Nodes actually searched for (not just pulled in as a neighbour) — always
    // visible and always colored the same way, regardless of colorMode.
    entryPointIds: { type: Array, default: () => [] }
})

const emit = defineEmits(['node-click', 'edge-click', 'background-click', 'ready'])

const containerEl = ref(null)
let cy = null
let nodeColor = {}
let nodeBorderColor = {}
// community id -> { bg, border } hsl() strings from clusterPalette, one per community
// currently in the graph. Rebuilt whenever the node set changes.
let clusterColors = {}
// Min/max of edge.weight (co-citation count) actually present in the current graph.
// Rebuilt whenever the edge set changes, so width always reflects relative strength
// within *this* graph — a static domain goes stale the moment filters change what
// range of weights is even possible (e.g. #181 raised the default minimum to 11,
// which alone exceeded the old hardcoded 1-10 domain).
let edgeWidthDomain = { min: 1, max: 1 }
// PageRank (Neo4j GDS, computed once globally over the whole dataset) has a long
// tail like co-citation counts do — a handful of major hub tools dominate, most
// nodes sit far lower — so sizing on a log scale (same reasoning as Sidebar.vue's
// occurrence slider) keeps the difference visible instead of a few hubs swallowing
// everyone else. null (not {min:0,max:0}) means "nothing in this graph has a real
// pageRank" — Publications never carry one (GDS only ran over Tool/Database), so a
// Publication-only graph falls back to NODE_SIZE_DEFAULT for every node.
const NODE_SIZE_MIN = 22
const NODE_SIZE_MAX = 46
const NODE_SIZE_DEFAULT = 34
let pageRankLogDomain = null

// Canvas fillStyle can't resolve CSS var(), so the custom properties from
// main.scss are read once and mirrored into plain hex values here.
function cssVar (name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

function computeEdgeWidthDomain () {
    if (!props.edges.length) return { min: 1, max: 1 }
    const weights = props.edges.map((edge) => edge.weight || 1)
    return { min: Math.min(...weights), max: Math.max(...weights) }
}

function computePageRankLogDomain () {
    const values = props.nodes
        .map((node) => node.properties?.pageRank)
        .filter((value) => typeof value === 'number' && value > 0)
    if (!values.length) return null
    return { min: Math.log(Math.min(...values)), max: Math.log(Math.max(...values)) }
}

function resolveNodeSize (data) {
    const pageRank = data.properties?.pageRank
    if (!pageRankLogDomain || typeof pageRank !== 'number' || pageRank <= 0) return NODE_SIZE_DEFAULT
    return mapRange(Math.log(pageRank), pageRankLogDomain.min, pageRankLogDomain.max, NODE_SIZE_MIN, NODE_SIZE_MAX)
}

function mapRange (value, domainMin, domainMax, rangeMin, rangeMax) {
    if (domainMax === domainMin) return rangeMax
    const clamped = Math.min(Math.max(value, domainMin), domainMax)
    return rangeMin + ((clamped - domainMin) / (domainMax - domainMin)) * (rangeMax - rangeMin)
}

// Shared by node fill and edge gradient stops, so an edge always fades between the
// exact colors its two endpoints are painted with — type or topic, whichever is active.
function resolveNodeFillColor (data) {
    if (props.colorMode === 'topic') {
        return clusterColors[data.properties?.community]?.bg || '#999999'
    }
    return nodeColor[data.type] || '#999999'
}

function resolveNodeBorderColor (data) {
    if (props.colorMode === 'topic') {
        return clusterColors[data.properties?.community]?.border || '#666666'
    }
    return nodeBorderColor[data.type] || '#666666'
}

// A node directly connected to 2+ active search hubs is a "bridge" — shared
// between searches. Only meaningful with 2+ hubs; a single-hub search has no
// bridges by definition. Returns { [bridgeNodeId]: Set<hubId> }.
function findBridgeHubs (edges, entryPointIds) {
    if (entryPointIds.length < 2) return {}
    const entryPointSet = new Set(entryPointIds)
    const connectedHubs = {}
    edges.forEach((edge) => {
        const source = String(edge.source)
        const target = String(edge.target)
        if (entryPointSet.has(source) && !entryPointSet.has(target)) {
            (connectedHubs[target] ??= new Set()).add(source)
        }
        if (entryPointSet.has(target) && !entryPointSet.has(source)) {
            (connectedHubs[source] ??= new Set()).add(target)
        }
    })
    return Object.fromEntries(Object.entries(connectedHubs).filter(([, hubs]) => hubs.size >= 2))
}

// Direct neighbours of a hub that are connected to it ALONE, not shared with
// another active search hub — the "spokes" that make up its own burst, as opposed
// to bridge nodes (2+ hubs, handled by repositionBridges() below). Returns
// { [hubId]: [leafId, ...] }.
function findExclusiveLeaves (edges, entryPointIds) {
    const entryPointSet = new Set(entryPointIds)
    const hubOf = {} // nodeId -> its one hub, or null once seen connected to 2+
    edges.forEach((edge) => {
        const source = String(edge.source)
        const target = String(edge.target)
        if (entryPointSet.has(source) && !entryPointSet.has(target)) {
            hubOf[target] = (target in hubOf && hubOf[target] !== source) ? null : source
        }
        if (entryPointSet.has(target) && !entryPointSet.has(source)) {
            hubOf[source] = (source in hubOf && hubOf[source] !== target) ? null : target
        }
    })
    const groups = {}
    Object.entries(hubOf).forEach(([id, hubId]) => {
        if (hubId) (groups[hubId] ??= []).push(id)
    })
    return groups
}

// Neighbour offsets (hub-relative x/y) computed once from the real post-pass-1
// positions, before anything moves — the rest of separateHubs() only needs how
// far a hub's burst reaches in a given DIRECTION (see radiusToward below), not an
// absolute position, and translating a hub later doesn't change this shape.
function hubNeighborOffsets (hubId) {
    const hubPos = cy.getElementById(hubId).position()
    return cy.getElementById(hubId).neighborhood('node').map((node) => {
        const pos = node.position()
        return { x: pos.x - hubPos.x, y: pos.y - hubPos.y }
    })
}

// How far a hub's burst extends along one direction (ux,uy must be a unit vector):
// the scalar projection of its farthest-reaching neighbour onto that axis. NOT the
// farthest neighbour in any direction — a hub's burst is rarely a neat circle, and
// a handful of outliers pointing AWAY from the other hub made an omnidirectional
// radius look generous even while the dense core actually facing the other hub
// still overlapped (confirmed by testing both versions). Projecting onto the
// hub-to-hub axis measures clearance where it's actually needed.
function radiusToward (offsets, ux, uy) {
    let max = 0
    offsets.forEach(({ x, y }) => {
        const projection = x * ux + y * uy
        if (projection > max) max = projection
    })
    return max
}

const HUB_SEPARATION_MARGIN = 100
const SEPARATION_ITERATIONS = 6

// Pairwise relaxation, not a closed-form solve: pushing hub A and B apart to
// satisfy their pair alone can reintroduce overlap with a third hub C once 3+
// search hubs are active, so this repeats a few passes until distances settle —
// cheap even at a handful of hubs, unlike re-running fcose itself. The direction
// between a pair changes as they're pushed apart, so radiusToward() is recomputed
// against the CURRENT axis each time, not cached from the first pass.
function computeHubTargets (entryPointIds, offsetsByHub) {
    const positions = {}
    entryPointIds.forEach((id) => { positions[id] = { ...cy.getElementById(id).position() } })

    for (let iter = 0; iter < SEPARATION_ITERATIONS; iter++) {
        for (let i = 0; i < entryPointIds.length; i++) {
            for (let j = i + 1; j < entryPointIds.length; j++) {
                const a = entryPointIds[i]
                const b = entryPointIds[j]
                const dx = positions[b].x - positions[a].x
                const dy = positions[b].y - positions[a].y
                const dist = Math.hypot(dx, dy) || 1
                const ux = dx / dist
                const uy = dy / dist
                const minDist = radiusToward(offsetsByHub[a], ux, uy) +
                    radiusToward(offsetsByHub[b], -ux, -uy) + HUB_SEPARATION_MARGIN
                if (dist < minDist) {
                    const push = (minDist - dist) / 2
                    positions[a].x -= ux * push
                    positions[a].y -= uy * push
                    positions[b].x += ux * push
                    positions[b].y += uy * push
                }
            }
        }
    }
    return positions
}

// Translates each hub and its own exclusive leaves together, rigid-body style, so
// the burst fcose already organized well in pass 1 is preserved exactly — only its
// position shifts, nothing about its internal arrangement is redone. Repulsion
// alone (nodeRepulsion) can't guarantee this: two hubs sharing many bridge nodes
// pull toward each other via those shared springs regardless of how high repulsion
// is turned up, so a deterministic correction is needed instead of hoping the
// physics settles far enough apart on its own. Bridge nodes are excluded here —
// repositionBridges() places them afterward, once hubs are at their final spot.
//
// Two fancier versions of this (whole-cluster rotation to face away from other
// hubs, then an angle-compressing "fan" to open a gap on that side) were tried
// and reverted — kept simple on purpose for now.
function separateHubs (entryPointIds, exclusiveLeaves) {
    if (entryPointIds.length < 2) return
    const offsetsByHub = {}
    entryPointIds.forEach((id) => { offsetsByHub[id] = hubNeighborOffsets(id) })
    const targets = computeHubTargets(entryPointIds, offsetsByHub)

    entryPointIds.forEach((hubId) => {
        const from = cy.getElementById(hubId).position()
        const to = targets[hubId]
        const dx = to.x - from.x
        const dy = to.y - from.y
        if (!dx && !dy) return
        cy.getElementById(hubId).position(to)
        ;(exclusiveLeaves[hubId] || []).forEach((leafId) => {
            const leaf = cy.getElementById(leafId)
            const pos = leaf.position()
            leaf.position({ x: pos.x + dx, y: pos.y + dy })
        })
    })
}

// Nodes sharing the exact same hub set would otherwise all land on one centroid —
// spaced out along the line perpendicular to the hub-to-hub axis instead, so a
// whole group of bridges (e.g. publications co-cited by both "blast" and
// "1000Genomes") fans out into a small row instead of collapsing into one
// overlapping, tangled knot.
const BRIDGE_SPACING = 45

// Moves each bridge node near the hubs it's connected to, using their REAL final
// positions (post separateHubs()) — not a guess at where they'd end up. Grouped by
// exact hub-set so a 3+ hub search doesn't average together bridges that actually
// belong near different hub pairs.
function repositionBridges (bridgeHubs) {
    const groups = {}
    Object.entries(bridgeHubs).forEach(([id, hubIds]) => {
        const key = [...hubIds].sort().join(',')
        ;(groups[key] ??= []).push(id)
    })

    Object.values(groups).forEach((ids) => {
        const hubIds = [...bridgeHubs[ids[0]]]
        const positions = hubIds.map((hubId) => cy.getElementById(hubId).position())
        const centroid = {
            x: positions.reduce((sum, p) => sum + p.x, 0) / positions.length,
            y: positions.reduce((sum, p) => sum + p.y, 0) / positions.length
        }
        const [a, b] = positions
        const dx = (b || { x: a.x + 1, y: a.y }).x - a.x
        const dy = (b || { x: a.x + 1, y: a.y }).y - a.y
        const len = Math.hypot(dx, dy) || 1
        const perpX = -dy / len
        const perpY = dx / len

        ids.forEach((id, index) => {
            const offset = (index - (ids.length - 1) / 2) * BRIDGE_SPACING
            cy.getElementById(id).position({
                x: centroid.x + perpX * offset,
                y: centroid.y + perpY * offset
            })
        })
    })
}

// A Publication is a "bridge" once it's connected to 2+ distinct Tool/Database
// nodes in the current graph — every edge touching that publication is then
// flagged, not just the "extra" ones, since there's no way to single out which
// specific edge is the ambiguous one (see the edge[isPublicationBridge] style
// comment for why this matters). Recomputed whenever nodes/edges change, same as
// edgeWidthDomain/clusterColors above.
function computePublicationBridgeEdgeIds () {
    const typeById = new Map(props.nodes.map((node) => [String(node.id), node.type]))
    const isToolLike = (id) => typeById.get(id) === 'Tool' || typeById.get(id) === 'Database'

    const publicationNeighbors = new Map()
    props.edges.forEach((edge) => {
        const source = String(edge.source)
        const target = String(edge.target)
        let publicationId = null
        let neighborId = null
        if (typeById.get(source) === 'Publication' && isToolLike(target)) {
            publicationId = source
            neighborId = target
        } else if (typeById.get(target) === 'Publication' && isToolLike(source)) {
            publicationId = target
            neighborId = source
        }
        if (!publicationId) return
        if (!publicationNeighbors.has(publicationId)) publicationNeighbors.set(publicationId, new Set())
        publicationNeighbors.get(publicationId).add(neighborId)
    })

    const bridgePublicationIds = new Set(
        [...publicationNeighbors.entries()].filter(([, neighbors]) => neighbors.size >= 2).map(([id]) => id)
    )

    const bridgeEdgeIds = new Set()
    props.edges.forEach((edge) => {
        const source = String(edge.source)
        const target = String(edge.target)
        if (bridgePublicationIds.has(source) || bridgePublicationIds.has(target)) {
            bridgeEdgeIds.add(String(edge.id))
        }
    })
    return bridgeEdgeIds
}

function toElements () {
    const bridgeEdgeIds = computePublicationBridgeEdgeIds()
    const nodeEls = props.nodes.map((node) => ({
        group: 'nodes',
        data: { id: String(node.id), label: node.label, type: node.type, properties: node.properties }
    }))
    const edgeEls = props.edges.map((edge) => {
        const data = {
            id: String(edge.id),
            source: String(edge.source),
            target: String(edge.target),
            weight: edge.weight || 1,
            properties: edge.properties
        }
        // Cytoscape's edge[isPublicationBridge] selector matches on field *presence*,
        // not truthiness — isPublicationBridge: false would still count as "present"
        // and match every edge, which is exactly the all-dashed bug this avoids.
        if (bridgeEdgeIds.has(String(edge.id))) data.isPublicationBridge = true
        return { group: 'edges', data }
    })
    return [...nodeEls, ...edgeEls]
}

// nodeRepulsion/idealEdgeLength raised well above fcose's defaults (4500/50):
// dense hub-and-spoke searches (e.g. "blast", ~150 neighbours) need much more
// spacing to keep node labels from overlapping around the hub. idealEdgeLength
// (the spring rest length on every edge) sets how far each connected node sits
// from its hub; nodeRepulsion spaces out unconnected leaves from each other and
// from the hub. gravity (default 0.25) pulls every node toward the layout's
// center, which fights against both of those and compresses everything back
// inward — lowered so the extra repulsion/edge-length room actually shows up
// as overall spacing instead of being pulled back together.
function buildLayoutOptions (randomize) {
    return {
        name: 'fcose',
        animate: false,
        fit: true,
        // Without this, fcose only keeps the node *circles* from overlapping — the
        // (wider, uncounted) label beneath each one can still land on top of a
        // neighbouring node.
        nodeDimensionsIncludeLabels: true,
        nodeRepulsion: 22000,
        idealEdgeLength: 320,
        gravity: 0.12,
        randomize
    }
}

// Two passes: (1) a normal, fully-randomized fcose run that organizes the *whole*
// graph, with no awareness of hubs/bridges at all — identical to a single-hub
// search, so multi-hub searches get the same well-spread, non-overlapping bursts
// fcose already produces for one hub. (2) only with 2+ active search hubs AND at
// least one bridge node: separateHubs() deterministically pushes hub bursts apart
// (plain repulsion can't guarantee this — two hubs sharing many bridge nodes pull
// back together via those shared springs no matter how high repulsion goes),
// repositionBridges() places shared nodes near their real final hub positions,
// then a short *incremental* layout lets only the bridge nodes settle around those
// new positions.
//
// Everything except the bridges is explicitly locked for that second pass. Without
// this, fcose's incremental mode (still driven by the same nodeRepulsion/
// idealEdgeLength/gravity forces) quietly pulls the two separated hubs right back
// together over its ~2500 iterations, silently undoing separateHubs() — locking
// makes the second pass do only the one thing it's meant for.
function runLayoutSequence () {
    const firstPass = cy.layout(buildLayoutOptions(true))
    // .one() registered on the layout object itself (not cy), so it only fires for
    // this run.
    firstPass.one('layoutstop', () => {
        if (props.entryPointIds.length < 2) {
            // Screen.vue relies on "ready" to know the graph is actually settled, not
            // just that new data arrived, before turning off the loading overlay.
            emit('ready')
            return
        }
        const exclusiveLeaves = findExclusiveLeaves(props.edges, props.entryPointIds)
        separateHubs(props.entryPointIds, exclusiveLeaves)
        const bridgeHubs = findBridgeHubs(props.edges, props.entryPointIds)
        const bridgeIds = Object.keys(bridgeHubs)
        if (bridgeIds.length === 0) {
            emit('ready')
            return
        }
        repositionBridges(bridgeHubs)

        const bridgeIdSet = new Set(bridgeIds)
        cy.nodes().forEach((node) => {
            if (!bridgeIdSet.has(node.id())) node.lock()
        })
        const secondPass = cy.layout(buildLayoutOptions(false))
        secondPass.one('layoutstop', () => {
            cy.nodes().unlock()
            emit('ready')
        })
        secondPass.run()
    })
    firstPass.run()
}

// bg is passed explicitly because cy.png() renders on an offscreen canvas
// with a transparent background by default, not the page's CSS.
function exportPng () {
    return cy.png({ full: true, scale: 2, bg: cssVar('--insolito-bg') })
}

const ZOOM_STEP = 1.2
const PAN_STEP = 120
const PAN_MARGIN = 80

// Both zoom in/out re-center on the viewport's own center (not the graph's), matching
// the behaviour of scroll-to-zoom, which is already how zooming works via mouse/trackpad.
function zoomIn () {
    if (!cy) return
    cy.zoom({ level: cy.zoom() * ZOOM_STEP, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } })
}

function zoomOut () {
    if (!cy) return
    cy.zoom({ level: cy.zoom() / ZOOM_STEP, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } })
}

function fitView () {
    cy?.fit(undefined, 40)
}

// dx/dy are the direction the user wants to look toward (-1/0/1 per axis, e.g. the
// right-pan button passes dx=1), not raw pixels — Controls.vue passes the direction,
// this owns the actual step size. Negated before calling cy.panBy(): Cytoscape's pan
// is applied to the *content* (renderedPosition = modelPosition * zoom + pan), so
// increasing pan.x moves the content right, which reveals what's to the LEFT of the
// viewport — the opposite of what "pan right" should feel like to the user.
function panBy (dx, dy) {
    cy?.panBy({ x: -dx * PAN_STEP, y: -dy * PAN_STEP })
}

defineExpose({ exportPng, zoomIn, zoomOut, fitView, panBy })

// Toggles a class instead of removing elements, so hiding/showing a layer never
// re-triggers the layout — nodes stay exactly where they were. An edge is hidden
// whenever either endpoint is, regardless of the edge's own data.
function isEntryPoint (el) {
    return props.entryPointIds.includes(el.data('id'))
}

function applyVisibility () {
    if (!cy) return
    const visibility = { hiddenTypes: props.hiddenTypes, hiddenCommunities: props.hiddenCommunities, hiddenToolTypes: props.hiddenToolTypes, entryPointIds: props.entryPointIds }
    cy.batch(() => {
        cy.nodes().forEach((node) => {
            const hidden = isNodeHidden({ id: node.data('id'), type: node.data('type'), properties: node.data('properties') }, visibility)
            node.toggleClass('layer-hidden', hidden)
        })
        cy.edges().forEach((edge) => {
            edge.toggleClass('layer-hidden', edge.source().hasClass('layer-hidden') || edge.target().hasClass('layer-hidden'))
        })
    })
}

onMounted(() => {
    // The cytoscape constructor + its initial fcose layout run synchronously and can
    // block the main thread for a noticeable moment on a large restored graph — with
    // no network wait to cover it (unlike a fresh search), that would freeze the UI
    // between clicking "Explore" and the screen appearing. A single requestAnimationFrame
    // isn't enough — it still fires before the browser paints the current frame. setTimeout
    // pushes the work to a new macrotask, after the browser has had a chance to paint the
    // mounted screen (with its loading overlay) first.
    setTimeout(() => {
        for (const type of ['Tool', 'Database', 'Publication']) {
            const color = getTypeColor(type)
            nodeColor[type] = color.bg
            nodeBorderColor[type] = color.border
        }

        clusterColors = buildClusterColorMap(props.nodes)
        edgeWidthDomain = computeEdgeWidthDomain()
        pageRankLogDomain = computePageRankLogDomain()

        cy = cytoscape({
            container: containerEl.value,
            elements: toElements(),
            minZoom: 0.1,
            maxZoom: 4,
            // No layout run here — runLayoutSequence() (called below, once cy exists)
            // owns the actual layout so the mount path and the data-change path
            // (the watch() further down) share the exact same two-pass logic.
            layout: { name: 'preset' },
            style: [
                {
                    selector: 'node',
                    style: {
                        // Entry points match every other node in color and border-width — shape,
                        // size and label size/weight are the differentiators, plus the
                        // text-background halo just below (and that it's exempt from
                        // layer-hiding, applyVisibility()). round-diamond over plain diamond:
                        // same angular silhouette but softened corners, closer to the rounded
                        // feel used elsewhere (buttons, panels) than a sharp-cornered diamond.
                        shape: (el) => (isEntryPoint(el) ? 'round-diamond' : 'ellipse'),
                        'background-color': (el) => resolveNodeFillColor(el.data()),
                        'border-color': (el) => resolveNodeBorderColor(el.data()),
                        'border-width': (el) => (isEntryPoint(el) ? 4 : 2),
                        // Entry points keep their own fixed, emphasized size regardless of
                        // pageRank — they're already visually distinct (shape, border, label),
                        // and the whole point is that it's the node YOU searched for, not
                        // necessarily the most globally important one.
                        width: (el) => (isEntryPoint(el) ? 40 : resolveNodeSize(el.data())),
                        height: (el) => (isEntryPoint(el) ? 40 : resolveNodeSize(el.data())),
                        label: 'data(label)',
                        'font-size': (el) => (isEntryPoint(el) ? 14 : 12),
                        'font-weight': (el) => (isEntryPoint(el) ? 'bold' : 'normal'),
                        color: cssVar('--insolito-text'),
                        'text-valign': 'bottom',
                        'text-margin-y': 6,
                        // Entry point only: the hub's label sits right where edges converge,
                        // so a plain color fill can read as smeared by the lines behind it.
                        'text-background-opacity': (el) => (isEntryPoint(el) ? 0.75 : 0),
                        'text-background-color': cssVar('--insolito-bg'),
                        'text-background-shape': 'roundrectangle',
                        'text-background-padding': 4
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        width: (el) => mapRange(el.data('weight'), edgeWidthDomain.min, edgeWidthDomain.max, 1, 6),
                        'line-fill': 'linear-gradient',
                        'line-gradient-stop-colors': (el) => `${resolveNodeFillColor(el.source().data())} ${resolveNodeFillColor(el.target().data())}`,
                        // 'straight', not 'bezier': in a hub-and-spoke graph, bezier's default
                        // curvature makes edges toward nearby-clustered targets bow through the
                        // same corridor for most of their length, reading as several lines
                        // converging on one node when they're actually headed to different ones.
                        // Straight lines are each the direct hub->target path, so two edges to
                        // different nodes only ever touch at the shared hub endpoint.
                        'curve-style': 'straight'
                    }
                },
                {
                    // A Publication bridging 2+ Tools/Databases is a weaker signal than a
                    // direct Tool-Tool edge (CLAUDE.md: the two Tool-Publication edges are
                    // aggregated independently, so the graph can't tell whether the same
                    // third article produced both, or two unrelated ones did) — dashed so
                    // that ambiguity is visible, not just documented.
                    selector: 'edge[isPublicationBridge]',
                    style: {
                        'line-style': 'dashed',
                        'line-dash-pattern': [6, 3]
                    }
                },
                {
                    // Canvas elements get no native CSS :hover — this plus the cursor
                    // toggle below (mouseover/mouseout handlers) is the only affordance
                    // that a node/edge is clickable.
                    selector: 'node.hovered',
                    style: {
                        'border-width': (el) => (isEntryPoint(el) ? 6 : 4),
                        'overlay-opacity': 0.15,
                        'overlay-color': cssVar('--insolito-primary'),
                        'overlay-padding': 4
                    }
                },
                {
                    selector: 'edge.hovered',
                    style: {
                        width: (el) => mapRange(el.data('weight'), edgeWidthDomain.min, edgeWidthDomain.max, 1, 6) + 2
                    }
                },
                {
                    selector: '.layer-hidden',
                    style: { display: 'none' }
                }
            ]
        })

        // Keeps at least PAN_MARGIN px of the graph's bounding box on screen at all
        // times — without this, drag-panning (or the Controls D-pad) can push the
        // whole graph off the canvas with no way back except Reset. Re-entrant guard
        // because cy.panBy() below fires its own 'pan' event synchronously.
        let clampingPan = false
        function clampPan () {
            if (!cy || clampingPan) return
            const bb = cy.elements().boundingBox()
            if (!Number.isFinite(bb.x1)) return
            const zoom = cy.zoom()
            const pan = cy.pan()
            const w = cy.width()
            const h = cy.height()
            const x1 = bb.x1 * zoom + pan.x
            const x2 = bb.x2 * zoom + pan.x
            const y1 = bb.y1 * zoom + pan.y
            const y2 = bb.y2 * zoom + pan.y

            let dx = 0
            let dy = 0
            if (x2 < PAN_MARGIN) dx = PAN_MARGIN - x2
            else if (x1 > w - PAN_MARGIN) dx = (w - PAN_MARGIN) - x1
            if (y2 < PAN_MARGIN) dy = PAN_MARGIN - y2
            else if (y1 > h - PAN_MARGIN) dy = (h - PAN_MARGIN) - y1

            if (dx || dy) {
                clampingPan = true
                cy.panBy({ x: dx, y: dy })
                clampingPan = false
            }
        }
        cy.on('pan zoom', clampPan)

        // Viewport-relative (not container-relative) click point, so the caller can
        // anchor a fixed-position panel directly off clientX/clientY without also
        // needing the container's own offset in the page.
        function clickPosition (event) {
            const rect = containerEl.value.getBoundingClientRect()
            return { x: rect.left + event.renderedPosition.x, y: rect.top + event.renderedPosition.y }
        }

        cy.on('mouseover', 'node, edge', (event) => {
            event.target.addClass('hovered')
            containerEl.value.style.cursor = 'pointer'
        })
        cy.on('mouseout', 'node, edge', (event) => {
            event.target.removeClass('hovered')
            containerEl.value.style.cursor = ''
        })

        cy.on('tap', 'node', (event) => {
            emit('node-click', { ...event.target.data(), clickPosition: clickPosition(event) })
        })

        cy.on('tap', 'edge', (event) => {
            emit('edge-click', { ...event.target.data(), clickPosition: clickPosition(event) })
        })

        cy.on('tap', (event) => {
            if (event.target === cy) {
                emit('background-click')
            }
        })

        // Skip the layout (and its 'ready' emission) when mounting with nothing to
        // lay out. Harmless on a normal visit (no search is in flight yet at this
        // point), but on a Share-link/JSON-import restore — where restoreFromMetadata
        // sets uiStore.rebuilding=true before this component's data even arrives —
        // this mount can race a real search already in progress. Without this guard,
        // this empty layout's spurious 'ready' turns uiStore.busy off immediately,
        // long before the real search resolves, and the loading overlay never shows
        // for the actual wait (see CLAUDE.md resume log for #211's Share round-trip fix).
        if (props.nodes.length) {
            runLayoutSequence()
            applyVisibility()
        }
    }, 0)
})

watch([() => props.nodes, () => props.edges], () => {
    if (!cy) return
    // Deferred so the browser gets to paint the "Building graph…" phase text (set by
    // Sidebar.vue right before this data change) before the synchronous, blocking
    // cy.add() + runLayoutSequence() computation runs — without this gap the phase
    // flips and the layout finishes within the same tick, so the text never
    // actually renders.
    setTimeout(() => {
        clusterColors = buildClusterColorMap(props.nodes)
        edgeWidthDomain = computeEdgeWidthDomain()
        pageRankLogDomain = computePageRankLogDomain()
        cy.elements().remove()
        cy.add(toElements())
        runLayoutSequence()
        applyVisibility()
    }, 0)
}, { deep: true })

// Style functions read props.colorMode directly, but Cytoscape only re-evaluates them
// on its own triggers (data/element changes) — switching modes needs an explicit nudge.
watch(() => props.colorMode, () => {
    cy?.style().update()
    applyVisibility()
})

watch([() => props.hiddenTypes, () => props.hiddenCommunities, () => props.hiddenToolTypes], () => {
    applyVisibility()
}, { deep: true })

// entryPointIds affects both which nodes are exempt from hiding and their color.
watch(() => props.entryPointIds, () => {
    cy?.style().update()
    applyVisibility()
}, { deep: true })

onUnmounted(() => {
    cy?.destroy()
    cy = null
})
</script>

<style scoped>
.graph-network {
    width: 100%;
    height: 100%;
}
</style>
