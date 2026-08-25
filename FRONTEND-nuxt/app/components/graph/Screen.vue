<template>
  <div class="graph-screen">
    <GraphSidebar ref="sidebarRef" :open="uiStore.sidebarOpen" @reset="onReset" @export-png="onExportPng" @go-home="$emit('go-home')" />

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
      <GraphControls
        v-if="graphStore.nodes.length"
        @pan="onPan"
        @fit="onFit"
        @zoom-in="onZoomIn"
        @zoom-out="onZoomOut"
      />
      <div v-if="uiStore.busy" class="graph-loading-overlay">
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
        <span class="graph-loading-text">{{ loadingText }}</span>
      </div>
      <div v-if="statusState === 'error'" class="graph-status">
        <svg viewBox="0 0 100 100" class="graph-status-icon" aria-hidden="true">
          <line x1="20" y1="50" x2="38" y2="50" class="graph-status-icon-edge-error" />
          <line x1="62" y1="50" x2="80" y2="50" class="graph-status-icon-edge-error" />
          <circle cx="20" cy="50" r="8" class="graph-status-icon-node-error" />
          <circle cx="80" cy="50" r="8" class="graph-status-icon-node-error" />
        </svg>
        <h2 class="graph-status-title">Couldn't reach the database</h2>
        <p class="graph-status-description">{{ uiStore.connectionError }}</p>
        <div class="graph-status-actions">
          <BButton variant="outline-secondary" @click="onRetry">Try again</BButton>
        </div>
      </div>
      <div v-else-if="statusState === 'empty'" class="graph-status">
        <svg viewBox="0 0 100 100" class="graph-status-icon" aria-hidden="true">
          <g class="graph-status-icon-edges graph-status-icon-edges-muted">
            <line x1="50" y1="50" x2="18" y2="32" />
            <line x1="50" y1="50" x2="80" y2="24" />
            <line x1="50" y1="50" x2="24" y2="80" />
            <line x1="50" y1="50" x2="78" y2="76" />
          </g>
          <circle cx="50" cy="50" r="9" class="graph-status-icon-node-outline" />
          <circle cx="18" cy="32" r="6" class="graph-status-icon-node-outline" />
          <circle cx="80" cy="24" r="6" class="graph-status-icon-node-outline" />
          <circle cx="24" cy="80" r="6" class="graph-status-icon-node-outline" />
          <circle cx="78" cy="76" r="6" class="graph-status-icon-node-outline" />
        </svg>
        <h2 class="graph-status-title">No results with these filters</h2>
        <p class="graph-status-description">Try widening the year range or lowering the minimum co-citations.</p>
        <div class="graph-status-actions">
          <BButton variant="outline-secondary" @click="onResetFilters">Reset filters</BButton>
        </div>
      </div>
      <div v-else-if="statusState === 'initial'" class="graph-status">
        <svg viewBox="0 0 100 100" class="graph-status-icon" aria-hidden="true">
          <g class="graph-status-icon-edges">
            <line x1="50" y1="50" x2="18" y2="32" />
            <line x1="50" y1="50" x2="80" y2="24" />
            <line x1="50" y1="50" x2="24" y2="80" />
            <line x1="50" y1="50" x2="78" y2="76" />
          </g>
          <circle cx="50" cy="50" r="9" class="graph-status-icon-hub" />
          <circle cx="18" cy="32" r="6" class="graph-status-icon-node" />
          <circle cx="80" cy="24" r="6" class="graph-status-icon-node" />
          <circle cx="24" cy="80" r="6" class="graph-status-icon-node" />
          <circle cx="78" cy="76" r="6" class="graph-status-icon-node" />
        </svg>
        <h2 class="graph-status-title">Start exploring</h2>
        <p class="graph-status-description">Search for a tool, database, or topic in the sidebar to see how it connects in the literature.</p>
        <div class="graph-status-actions graph-status-examples">
          <button
            v-for="example in exampleSearches"
            :key="example.kind"
            type="button"
            class="graph-status-chip"
            @click="onExampleClick(example)"
          >
            {{ example.name }}
          </button>
        </div>
      </div>
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
        @ready="onNetworkReady"
      />
    </main>

    <GraphHowToUseModal :model-value="uiStore.howToOpen" @update:model-value="uiStore.setHowToOpen($event)" />
  </div>
</template>

<script setup>
defineEmits(['go-home'])

const graphStore = useGraphStore()
const uiStore = useUiStore()

const selectedNode = ref(null)
const networkRef = ref(null)
const sidebarRef = ref(null)

// Verified against DB/ToolTopicAutocomplete.json — exact casing matters, resolveSearchTerm
// only normalizes case for typed input, addSearchTerm expects the canonical value.
// One pool per kind (not one mixed pool) so the 3 examples always cover Tool +
// Database + Topic — showing all 3 searchable kinds, not whichever the dice picked.
const EXAMPLE_POOL = {
    Tool: ['blast', 'SAMtools', 'BWA', 'bowtie2', 'megahit', 'IGV', 'GATK', 'Trimmomatic', 'MAFFT', 'MUSCLE', 'MEGA'],
    Database: ['Ensembl', '1000Genomes', 'PDBe', 'ChEMBL', 'STRING', 'SRA', 'InterPro', 'Pfam', 'Reactome', 'ArrayExpress'],
    Topic: ['Sequence analysis', 'Genomics', 'Proteomics', 'Metagenomics', 'Phylogenetics']
}

function pickExamples () {
    return Object.entries(EXAMPLE_POOL).map(([kind, names]) => ({
        kind,
        name: names[Math.floor(Math.random() * names.length)]
    }))
}

// Reshuffled on mount and again in onReset() below — every time the initial state
// comes back on screen — not memoized, so the 3 examples aren't always the same.
const exampleSearches = ref(pickExamples())

// Precedence matters: a connection error takes over even though searchTerms is
// also non-empty at that point (the failed term was already added optimistically),
// otherwise it would fall through to the "empty" case and show a misleading
// "no results" message instead of explaining the actual failure.
const statusState = computed(() => {
    if (graphStore.nodes.length > 0 || uiStore.busy) return null
    if (uiStore.connectionError) return 'error'
    if (graphStore.searchTerms.length) return 'empty'
    return 'initial'
})

function onRetry () {
    sidebarRef.value?.retrySearch()
}

function onResetFilters () {
    sidebarRef.value?.resetFilters()
}

function onExampleClick (example) {
    sidebarRef.value?.runExampleSearch(example)
}
// Only true right when this screen mounts with an already-populated graph (i.e.
// returning from landing via "Explore", not a fresh search) — cleared once
// GraphNetwork's initial layout settles. False when there's nothing to restore.
uiStore.setRestoringGraph(graphStore.nodes.length > 0)

const loadingText = computed(() => {
    if (!uiStore.rebuilding) return 'Restoring graph…'
    return uiStore.rebuildPhase === 'building' ? 'Building graph…' : 'Searching…'
})

function onReset () {
    graphStore.reset()
    uiStore.resetLayers()
    selectedNode.value = null
    exampleSearches.value = pickExamples()
}

function onExportPng () {
    const dataUri = networkRef.value?.exportPng()
    if (dataUri) downloadDataUri(dataUri, 'InSoLiTo-network.png')
}

function onPan (dx, dy) {
    networkRef.value?.panBy(dx, dy)
}

function onFit () {
    networkRef.value?.fitView()
}

function onZoomIn () {
    networkRef.value?.zoomIn()
}

function onZoomOut () {
    networkRef.value?.zoomOut()
}

// Fires whenever GraphNetwork's layout settles — both the initial mount (restoring
// a graph from landing) and every subsequent relayout triggered by a search. Rebuilding
// is only cleared here, not right after the fetch, so the sidebar (search button,
// sliders) stays disabled for the full duration the main thread is actually busy.
function onNetworkReady () {
    uiStore.setRestoringGraph(false)
    uiStore.setRebuilding(false)
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

/* No box/shadow on purpose — a boxed card at this size read as a stray alert
   banner. Presence comes from the icon's scale and the type hierarchy instead,
   same restrained language as the rest of the app (Legend, NodeInfoPanel use
   real cards because they sit beside content; this sits alone in empty space). */
.graph-status {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 5;
    width: min(420px, calc(100vw - 48px));
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    text-align: center;
}

.graph-status-icon {
    width: 96px;
    height: 96px;
    margin-bottom: 8px;
}

.graph-status-title {
    margin: 0;
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--insolito-text);
}

.graph-status-description {
    margin: 0;
    font-size: 0.92rem;
    line-height: 1.5;
    color: var(--insolito-text-muted);
}

.graph-status-actions {
    margin-top: 8px;
}

/* Initial state: solid filled nodes/edges — a ready, connected cluster. */
.graph-status-icon-edges line {
    stroke: var(--insolito-edge);
    stroke-width: 2;
}

.graph-status-icon-hub {
    fill: var(--insolito-primary-dark);
}

.graph-status-icon-node {
    fill: var(--insolito-primary);
}

/* Empty-results state: same cluster, dashed edges and hollow nodes — the
   structure is there conceptually, nothing populated it under these filters. */
.graph-status-icon-edges-muted line {
    stroke: var(--insolito-border);
    stroke-dasharray: 4 4;
}

.graph-status-icon-node-outline {
    fill: var(--insolito-bg);
    stroke: var(--insolito-text-muted);
    stroke-width: 2;
}

/* Error state: just two nodes with a broken edge — the connection itself failed. */
.graph-status-icon-edge-error {
    stroke: var(--insolito-danger);
    stroke-width: 2;
}

.graph-status-icon-node-error {
    fill: none;
    stroke: var(--insolito-danger);
    stroke-width: 2;
}

.graph-status-examples {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;
}

.graph-status-chip {
    padding: 7px 16px;
    border: 1px solid var(--insolito-border);
    border-radius: 999px;
    background: var(--insolito-bg);
    color: var(--insolito-primary);
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s ease, border-color 0.15s ease;
}

.graph-status-chip:hover {
    background: var(--insolito-bg-footer);
    border-color: var(--insolito-primary);
}

@media (max-width: 600px) {
    .graph-status-icon {
        width: 72px;
        height: 72px;
    }

    .graph-status-title {
        font-size: 1.1rem;
    }
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
