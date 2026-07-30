<template>
  <div class="graph-legend">
    <div class="legend-header">
      <div class="legend-mode-toggle" role="tablist" aria-label="Legend color mode">
        <button
          type="button"
          role="tab"
          class="legend-mode-btn"
          :class="{ 'legend-mode-btn-active': uiStore.colorMode === 'type' }"
          :aria-selected="uiStore.colorMode === 'type'"
          @click="uiStore.setColorMode('type')"
        >
          By type
        </button>
        <button
          type="button"
          role="tab"
          class="legend-mode-btn"
          :class="{ 'legend-mode-btn-active': uiStore.colorMode === 'topic' }"
          :aria-selected="uiStore.colorMode === 'topic'"
          @click="uiStore.setColorMode('topic')"
        >
          By topic
        </button>
      </div>
      <button
        class="legend-collapse-btn"
        :aria-expanded="uiStore.legendOpen"
        aria-label="Toggle legend"
        @click="uiStore.toggleLegend()"
      >
        <svg
          viewBox="0 0 24 24"
          class="legend-chevron"
          :class="{ 'legend-chevron-collapsed': !uiStore.legendOpen }"
        >
          <path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
    </div>

    <ul v-if="uiStore.legendOpen && uiStore.colorMode === 'type'" class="legend-list">
      <li>
        <span class="legend-dot legend-dot-tool" />
        Tool
      </li>
      <li>
        <span class="legend-dot legend-dot-database" />
        Database
      </li>
      <li>
        <span class="legend-dot legend-dot-publication" />
        Publication
      </li>
    </ul>

    <ul v-else-if="uiStore.legendOpen" class="legend-list">
      <li v-for="entry in topicEntries" :key="entry.id">
        <span class="legend-dot" :style="{ background: entry.bg, borderColor: entry.border }" />
        {{ entry.label }}
      </li>
      <li v-if="topicEntries.length === 0" class="legend-empty">
        No clusters to show yet.
      </li>
    </ul>
  </div>
</template>

<script setup>
const uiStore = useUiStore()
const graphStore = useGraphStore()

// Colors come from clusterPalette's buildClusterColorMap (same helper Network.vue uses)
// so a community's swatch here always matches its color on the canvas — every
// community present gets its own reproducible color, sorted by node count
// (largest cluster first), matching the old app's cluster legend.
const topicEntries = computed(() => {
    const nodes = graphStore.nodes
    const colorMap = buildClusterColorMap(nodes)
    const counts = {}
    nodes.forEach((node) => {
        const id = node.properties?.community
        if (id === undefined || id === null) return
        counts[id] = (counts[id] || 0) + 1
    })

    return Object.entries(counts)
        .map(([id, count]) => ({
            id,
            label: communityTopicById[id] || `Cluster ${id}`,
            count,
            bg: colorMap[id].bg,
            border: colorMap[id].border
        }))
        .sort((a, b) => b.count - a.count)
})
</script>

<style scoped>
.graph-legend {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 18;
    width: 220px;
    box-sizing: border-box;
    background: var(--insolito-bg);
    border-radius: 8px;
    border-top: 4px solid var(--insolito-border);
    box-shadow: 0 6px 24px rgba(28, 43, 58, 0.24);
    overflow: hidden;
}

.legend-header {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 8px;
}

.legend-mode-toggle {
    flex: 1;
    display: flex;
    gap: 2px;
    background: var(--insolito-bg-footer);
    border-radius: 6px;
    padding: 2px;
}

.legend-mode-btn {
    flex: 1;
    padding: 5px 6px;
    background: none;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--insolito-text-muted);
    white-space: nowrap;
}

.legend-mode-btn-active {
    background: var(--insolito-primary);
    color: white;
}

.legend-collapse-btn {
    flex-shrink: 0;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: none;
    border: none;
    cursor: pointer;
    color: var(--insolito-text);
}

.legend-chevron {
    width: 16px;
    height: 16px;
    transition: transform 0.2s ease;
}

.legend-chevron-collapsed {
    transform: rotate(-90deg);
}

.legend-list {
    list-style: none;
    margin: 0;
    padding: 0 16px 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 220px;
    overflow-y: auto;
}

.legend-list li {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    color: var(--insolito-text);
}

.legend-empty {
    color: var(--insolito-text-muted);
    font-size: 0.82rem;
}

.legend-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
    box-sizing: border-box;
    border-width: 2px;
    border-style: solid;
}

.legend-dot-tool {
    background: var(--insolito-node-primary);
    border-color: var(--insolito-primary);
}

.legend-dot-database {
    background: var(--insolito-node-tertiary);
    border-color: var(--insolito-node-tertiary-dark);
}

.legend-dot-publication {
    background: var(--insolito-node-secondary);
    border-color: var(--insolito-secondary-hover);
}

@media (max-width: 600px) {
    .graph-legend {
        /* Clears the toggle button (top:20px, 40px tall) instead of overlapping it */
        top: 76px;
        left: 16px;
        right: 16px;
        width: auto;
    }
}
</style>
