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
      <div v-if="uiStore.rebuilding" class="graph-loading-overlay">
        <svg viewBox="0 0 80 80" class="graph-loading-svg" aria-hidden="true">
          <g class="graph-loading-edges">
            <line x1="40" y1="40" x2="12" y2="24" />
            <line x1="40" y1="40" x2="66" y2="18" />
            <line x1="40" y1="40" x2="20" y2="64" />
            <line x1="40" y1="40" x2="62" y2="60" />
          </g>
          <g class="graph-loading-nodes">
            <circle cx="40" cy="40" r="7" class="loading-node loading-node-hub" />
            <circle cx="12" cy="24" r="5" class="loading-node" style="animation-delay:0.15s" />
            <circle cx="66" cy="18" r="5" class="loading-node" style="animation-delay:0.3s" />
            <circle cx="20" cy="64" r="5" class="loading-node" style="animation-delay:0.45s" />
            <circle cx="62" cy="60" r="5" class="loading-node" style="animation-delay:0.6s" />
          </g>
        </svg>
        <span class="graph-loading-text">Searching…</span>
      </div>
      <p v-if="graphStore.nodes.length === 0 && !uiStore.rebuilding" class="graph-empty-state">
        {{ graphStore.searchTerms.length
          ? 'No results found for the current search and filters.'
          : 'Search for a tool, database, or topic in the sidebar to get started.' }}
      </p>
      <GraphNetwork
        ref="networkRef"
        :nodes="graphStore.nodes"
        :edges="graphStore.edges"
        :color-mode="uiStore.colorMode"
        :hidden-types="uiStore.hiddenTypes"
        :hidden-communities="uiStore.hiddenCommunities"
        :entry-point-ids="graphStore.entryPointIds"
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
    uiStore.resetLayers()
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

.graph-loading-overlay {
    position: absolute;
    inset: 0;
    z-index: 6;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 14px;
    background: rgba(255, 255, 255, 0.90);
    pointer-events: none;
}

.graph-loading-text {
    color: var(--insolito-text);
    font-size: 1.1rem;
    font-weight: 600;
}

.graph-loading-svg {
    width: 72px;
    height: 72px;
}

.graph-loading-edges line {
    stroke: var(--insolito-edge);
    stroke-width: 1.5;
}

.loading-node {
    fill: var(--insolito-primary);
    transform-origin: center;
    transform-box: fill-box;
    animation: graph-loading-node-pulse 1.2s ease-in-out infinite;
}

.loading-node-hub {
    fill: var(--insolito-primary-dark);
    animation: none;
}

@keyframes graph-loading-node-pulse {
    0%, 100% {
        transform: scale(1);
        opacity: 0.6;
    }
    50% {
        transform: scale(1.4);
        opacity: 1;
    }
}
</style>
