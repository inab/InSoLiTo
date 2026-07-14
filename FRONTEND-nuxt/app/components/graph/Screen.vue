<template>
  <div class="graph-screen">
    <GraphSidebar :open="sidebarOpen" @reset="graphStore.reset()" />

    <div v-if="sidebarOpen" class="sidebar-backdrop" @click="sidebarOpen = false" />

    <button
      class="sidebar-toggle"
      :class="{ 'sidebar-toggle-open': sidebarOpen }"
      :aria-expanded="sidebarOpen"
      aria-label="Close/Open menu"
      @click="sidebarOpen = !sidebarOpen"
    >
      <svg viewBox="0 0 24 24" class="sidebar-toggle-icon" :class="{ flipped: sidebarOpen }">
        <path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </button>

    <main class="graph-main" :class="sidebarOpen ? 'graph-main-with-sidebar' : 'graph-main-without-sidebar'">
      <p class="graph-hint">
        {{ clickedNodeLabel ? `Clicked: ${clickedNodeLabel}` : 'Click a node to test the wrapper.' }}
      </p>
      <GraphNetwork :nodes="graphStore.nodes" :edges="graphStore.edges" class="graph-canvas" @node-click="onNodeClick" />
    </main>
  </div>
</template>

<script setup>
const graphStore = useGraphStore()

const sidebarOpen = ref(false)
const clickedNodeLabel = ref('')

// Seeds the store with placeholder data until the Cypher queries are wired
// in (plan step 11). Each node carries its full `properties` object, same
// shape Neo4j will eventually send, so the store doesn't need a redesign
// when new fields (pageRank, doi, etc.) start getting used in the UI.
const mockNodes = [
    { id: 1, label: 'BLAST', type: 'Tool', properties: { label: 'blast', pageRank: 0.42, toolType: ['Tool'] } },
    { id: 2, label: 'BWA', type: 'Tool', properties: { label: 'bwa', pageRank: 0.31, toolType: ['Tool'] } },
    { id: 3, label: 'UniProt', type: 'Database', properties: { label: 'uniprot', pageRank: 0.55, toolType: ['Database'] } },
    { id: 4, label: 'Sample publication (2021)', type: 'Publication', properties: { title: 'Sample publication (2021)', year: 2021, doi: '10.1000/sample', pmid: '12345678' } },
    { id: 5, label: 'MEGA', type: 'Tool', properties: { label: 'mega', pageRank: 0.18, toolType: ['Tool'] } }
]
const mockEdges = [
    { id: 'e1', source: 1, target: 2, weight: 5, properties: { times: 5, year: 2019 } },
    { id: 'e2', source: 1, target: 3, weight: 2, properties: { times: 2, year: 2020 } },
    { id: 'e3', source: 2, target: 4, weight: 3, properties: { times: 3, year: 2021 } },
    { id: 'e4', source: 5, target: 1, weight: 4, properties: { times: 4, year: 2018 } }
]

function onNodeClick (data) {
    clickedNodeLabel.value = `${data.label} (pageRank: ${data.properties?.pageRank ?? 'n/a'})`
}

onMounted(() => {
    // Desktop starts with the sidebar open; narrow screens start closed (overlay pattern).
    if (!window.matchMedia('(max-width: 600px)').matches) {
        sidebarOpen.value = true
    }

    graphStore.setGraph(mockNodes, mockEdges)
})
</script>

<style scoped>
.graph-screen {
    --graph-sidebar-width: 300px;
    width: 100%;
    min-height: 100vh;
    background: var(--insolito-bg);
}

@media (max-width: 600px) {
    .graph-screen {
        /* Leaves room for the toggle button (40px + 16px gap) past the sidebar edge */
        --graph-sidebar-width: min(300px, calc(100vw - 56px));
    }
}

.sidebar-toggle {
    position: fixed;
    top: 20px;
    left: calc(var(--graph-sidebar-width) + 16px);
    z-index: 21;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--insolito-bg);
    border: 1px solid var(--insolito-border);
    border-radius: 50%;
    color: var(--insolito-primary);
    cursor: pointer;
    box-shadow: 0 2px 6px rgba(28, 43, 58, 0.12);
    transition: left 0.3s ease;
}

.sidebar-toggle:not(.sidebar-toggle-open) {
    left: 20px;
}

.sidebar-toggle-icon {
    width: 20px;
    height: 20px;
    transition: transform 0.3s ease;
}

.sidebar-toggle-icon.flipped {
    transform: rotate(180deg);
}

.graph-main {
    min-height: 100vh;
    transition: margin-left 0.3s ease;
}

.graph-main-with-sidebar {
    margin-left: var(--graph-sidebar-width);
}

.graph-main-without-sidebar {
    margin-left: 0;
}

.sidebar-backdrop {
    position: fixed;
    inset: 0;
    z-index: 19;
    background: rgba(28, 43, 58, 0.4);
    display: none;
}

@media (max-width: 600px) {
    .graph-main-with-sidebar {
        margin-left: 0;
    }

    .sidebar-backdrop {
        display: block;
    }
}

.graph-hint {
    position: fixed;
    top: 28px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 15;
    margin: 0;
    padding: 6px 16px;
    background: var(--insolito-bg);
    border: 1px solid var(--insolito-border);
    border-radius: 20px;
    color: var(--insolito-text-muted);
    font-size: 0.9rem;
}

.graph-canvas {
    height: 100vh;
}
</style>
