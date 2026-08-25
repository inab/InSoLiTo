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
    // Nodes actually searched for (not just pulled in as a neighbour) — always
    // visible and always colored the same way, regardless of colorMode.
    entryPointIds: { type: Array, default: () => [] }
})

const emit = defineEmits(['node-click', 'background-click', 'ready'])

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

function toElements () {
    const nodeEls = props.nodes.map((node) => ({
        group: 'nodes',
        data: { id: String(node.id), label: node.label, type: node.type, properties: node.properties }
    }))
    const edgeEls = props.edges.map((edge) => ({
        group: 'edges',
        data: {
            id: String(edge.id),
            source: String(edge.source),
            target: String(edge.target),
            weight: edge.weight || 1,
            properties: edge.properties
        }
    }))
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
const layoutOptions = {
    name: 'fcose',
    animate: false,
    fit: true,
    // Without this, fcose only keeps the node *circles* from overlapping — the
    // (wider, uncounted) label beneath each one can still land on top of a
    // neighbouring node.
    nodeDimensionsIncludeLabels: true,
    nodeRepulsion: 22000,
    idealEdgeLength: 320,
    gravity: 0.12
}

function runLayout () {
    // .one() registered on the layout object itself (not cy), so it only fires for
    // this run — Screen.vue relies on "ready" to know the graph is actually settled,
    // not just that new data arrived, before turning off the loading overlay.
    const layout = cy.layout(layoutOptions)
    layout.one('layoutstop', () => emit('ready'))
    layout.run()
}

// bg is passed explicitly because cy.png() renders on an offscreen canvas
// with a transparent background by default, not the page's CSS.
function exportPng () {
    return cy.png({ full: true, scale: 2, bg: cssVar('--insolito-bg') })
}

const ZOOM_STEP = 1.2
const PAN_STEP = 120

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
    const visibility = { hiddenTypes: props.hiddenTypes, hiddenCommunities: props.hiddenCommunities, entryPointIds: props.entryPointIds }
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

        cy = cytoscape({
            container: containerEl.value,
            elements: toElements(),
            ready: function () {
                // Fires once the initial layout (constructor's `layout` option) settles —
                // used by Screen.vue to know when a restored graph has finished laying out.
                this.one('layoutstop', () => emit('ready'))
            },
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
                        width: (el) => (isEntryPoint(el) ? 40 : 34),
                        height: (el) => (isEntryPoint(el) ? 40 : 34),
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
                    selector: '.layer-hidden',
                    style: { display: 'none' }
                }
            ],
            layout: layoutOptions
        })

        cy.on('tap', 'node', (event) => {
            emit('node-click', event.target.data())
        })

        cy.on('tap', (event) => {
            if (event.target === cy) {
                emit('background-click')
            }
        })

        applyVisibility()
    }, 0)
})

watch([() => props.nodes, () => props.edges], () => {
    if (!cy) return
    // Deferred so the browser gets to paint the "Building graph…" phase text (set by
    // Sidebar.vue right before this data change) before the synchronous, blocking
    // cy.add() + runLayout() computation runs — without this gap the phase flips and
    // the layout finishes within the same tick, so the text never actually renders.
    setTimeout(() => {
        clusterColors = buildClusterColorMap(props.nodes)
        edgeWidthDomain = computeEdgeWidthDomain()
        cy.elements().remove()
        cy.add(toElements())
        runLayout()
        applyVisibility()
    }, 0)
}, { deep: true })

// Style functions read props.colorMode directly, but Cytoscape only re-evaluates them
// on its own triggers (data/element changes) — switching modes needs an explicit nudge.
watch(() => props.colorMode, () => {
    cy?.style().update()
    applyVisibility()
})

watch([() => props.hiddenTypes, () => props.hiddenCommunities], () => {
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
