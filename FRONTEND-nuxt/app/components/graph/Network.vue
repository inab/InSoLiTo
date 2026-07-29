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
    edges: { type: Array, default: () => [] }
})

const emit = defineEmits(['node-click', 'background-click'])

const containerEl = ref(null)
let cy = null
let nodeColor = {}
let nodeBorderColor = {}

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
    cy.layout(layoutOptions).run()
}

onMounted(() => {
    nodeColor = {
        Tool: cssVar('--insolito-node-primary'),
        Database: cssVar('--insolito-node-tertiary'),
        Publication: cssVar('--insolito-node-secondary')
    }
    nodeBorderColor = {
        Tool: cssVar('--insolito-primary'),
        Database: cssVar('--insolito-node-tertiary-dark'),
        Publication: cssVar('--insolito-secondary-hover')
    }

    cy = cytoscape({
        container: containerEl.value,
        elements: toElements(),
        style: [
            {
                selector: 'node',
                style: {
                    'background-color': (el) => nodeColor[el.data('type')] || '#999999',
                    'border-width': 2,
                    'border-color': (el) => nodeBorderColor[el.data('type')] || '#666666',
                    label: 'data(label)',
                    'font-size': 12,
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
})

watch([() => props.nodes, () => props.edges], () => {
    if (!cy) return
    cy.elements().remove()
    cy.add(toElements())
    runLayout()
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
