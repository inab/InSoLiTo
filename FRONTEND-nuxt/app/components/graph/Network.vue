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

// Canvas fillStyle can't resolve CSS var(), so the custom properties from
// main.scss are read once and mirrored into plain hex values here.
function cssVar (name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
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
// spacing to keep node labels from overlapping around the hub.
const layoutOptions = {
    name: 'fcose',
    animate: false,
    fit: true,
    nodeRepulsion: 12000,
    idealEdgeLength: 150
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

defineExpose({ exportPng })

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
                        'background-color': (el) => {
                            if (props.colorMode === 'topic') {
                                return clusterColors[el.data('properties')?.community]?.bg || '#999999'
                            }
                            return nodeColor[el.data('type')] || '#999999'
                        },
                        'border-color': (el) => {
                            if (props.colorMode === 'topic') {
                                return clusterColors[el.data('properties')?.community]?.border || '#666666'
                            }
                            return nodeBorderColor[el.data('type')] || '#666666'
                        },
                        // Entry points stand out via a slightly bigger size + a slightly
                        // wider single border + bolder/bigger label — same fill color
                        // (type/topic) as every other node.
                        'border-width': (el) => (isEntryPoint(el) ? 4 : 2),
                        width: (el) => (isEntryPoint(el) ? 40 : 34),
                        height: (el) => (isEntryPoint(el) ? 40 : 34),
                        label: 'data(label)',
                        'font-size': (el) => (isEntryPoint(el) ? 14 : 12),
                        'font-weight': (el) => (isEntryPoint(el) ? 'bold' : 'normal'),
                        color: cssVar('--insolito-text'),
                        'text-valign': 'bottom',
                        'text-margin-y': 6
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        width: 'mapData(weight, 1, 10, 1, 6)',
                        'line-color': cssVar('--insolito-edge'),
                        'curve-style': 'bezier'
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
