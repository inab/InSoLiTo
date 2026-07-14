<template>
  <div class="graph-screen">
    <GraphSidebar :open="sidebarOpen" @reset="$emit('reset')" />

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
      <GraphNetwork :nodes="mockNodes" :edges="mockEdges" class="graph-canvas" @node-click="onNodeClick" />
    </main>
  </div>
</template>

<script setup>
defineEmits(['reset'])

const sidebarOpen = ref(false)
const clickedNodeLabel = ref('')

// Placeholder data until the Cypher queries are wired in (plan step 11).
const mockNodes = [
    { id: 1, label: 'BLAST', type: 'Tool' },
    { id: 2, label: 'BWA', type: 'Tool' },
    { id: 3, label: 'UniProt', type: 'Database' },
    { id: 4, label: 'Sample publication (2021)', type: 'Publication' },
    { id: 5, label: 'MEGA', type: 'Tool' }
]
const mockEdges = [
    { id: 'e1', source: 1, target: 2, weight: 5 },
    { id: 'e2', source: 1, target: 3, weight: 2 },
    { id: 'e3', source: 2, target: 4, weight: 3 },
    { id: 'e4', source: 5, target: 1, weight: 4 }
]

function onNodeClick (data) {
    clickedNodeLabel.value = data.label
}

onMounted(() => {
    // Desktop starts with the sidebar open; narrow screens start closed (overlay pattern).
    if (!window.matchMedia('(max-width: 600px)').matches) {
        sidebarOpen.value = true
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
