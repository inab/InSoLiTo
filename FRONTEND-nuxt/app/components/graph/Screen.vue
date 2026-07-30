<template>
  <div class="graph-screen">
    <GraphSidebar :open="uiStore.sidebarOpen" @reset="onReset" @export-png="onExportPng" />

    <div v-if="uiStore.sidebarOpen" class="sidebar-backdrop" @click="uiStore.setSidebarOpen(false)" />

    <button
      class="sidebar-toggle"
      :class="{ 'sidebar-toggle-open': uiStore.sidebarOpen }"
      :aria-expanded="uiStore.sidebarOpen"
      aria-label="Close/Open menu"
      @click="uiStore.toggleSidebar()"
    >
      <svg viewBox="0 0 24 24" class="sidebar-toggle-icon" :class="{ flipped: uiStore.sidebarOpen }">
        <path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </button>

    <main class="graph-main" :class="uiStore.sidebarOpen ? 'graph-main-with-sidebar' : 'graph-main-without-sidebar'">
      <GraphLegend v-if="graphStore.nodes.length" />
      <GraphNodeInfoPanel v-if="selectedNode" :node="selectedNode" @close="selectedNode = null" />
      <p v-if="graphStore.nodes.length === 0" class="graph-empty-state">
        Search for a tool or topic in the sidebar to get started.
      </p>
      <GraphNetwork
        ref="networkRef"
        :nodes="graphStore.nodes"
        :edges="graphStore.edges"
        class="graph-canvas"
        @node-click="selectedNode = $event"
        @background-click="selectedNode = null"
      />
    </main>
  </div>
</template>

<script setup>
const graphStore = useGraphStore()
const uiStore = useUiStore()

const selectedNode = ref(null)
const networkRef = ref(null)

function onReset () {
    graphStore.reset()
    selectedNode.value = null
}

function onExportPng () {
    const dataUri = networkRef.value?.exportPng()
    if (dataUri) downloadDataUri(dataUri, 'InSoLiTo-network.png')
}

onMounted(() => {
    // Desktop starts with the sidebar open; narrow screens start closed (overlay pattern).
    if (!window.matchMedia('(max-width: 600px)').matches) {
        uiStore.setSidebarOpen(true)
    }
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
    position: relative;
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

.graph-canvas {
    height: 100vh;
}

.graph-empty-state {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 5;
    color: var(--insolito-text-muted);
    font-size: 1rem;
    text-align: center;
    pointer-events: none;
}
</style>
