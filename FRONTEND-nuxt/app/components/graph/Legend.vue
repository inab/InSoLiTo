<template>
  <div class="graph-legend">
    <div class="legend-top-row">
      <span class="legend-title">Legend</span>
      <button
        class="legend-collapse-btn"
        :aria-expanded="uiStore.legendOpen"
        aria-label="Toggle legend"
        :disabled="uiStore.busy"
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

    <div class="legend-header">
      <div class="legend-mode-toggle" role="tablist" aria-label="Legend color mode">
        <button
          type="button"
          role="tab"
          class="legend-mode-btn"
          :class="{ 'legend-mode-btn-active': uiStore.colorMode === 'type' }"
          :aria-selected="uiStore.colorMode === 'type'"
          :disabled="uiStore.busy"
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
          :disabled="uiStore.busy"
          @click="uiStore.setColorMode('topic')"
        >
          By topic
        </button>
      </div>
    </div>

    <ul v-if="uiStore.legendOpen && uiStore.colorMode === 'type'" class="legend-list">
      <li v-for="type in TYPE_ENTRIES" :key="type.value">
        <button
          type="button"
          class="legend-item"
          :class="{ 'legend-item-hidden': uiStore.hiddenTypes.includes(type.value) }"
          :aria-pressed="!uiStore.hiddenTypes.includes(type.value)"
          :disabled="uiStore.busy"
          @click="uiStore.toggleHiddenType(type.value)"
        >
          <span class="legend-item-label">{{ type.label }}</span>
          <span
            class="legend-toggle"
            :class="[`legend-toggle-${type.value.toLowerCase()}`, { 'legend-toggle-off': uiStore.hiddenTypes.includes(type.value) }]"
          >
            <span class="legend-toggle-knob" />
          </span>
        </button>
      </li>
    </ul>

    <ul v-else-if="uiStore.legendOpen" class="legend-list">
      <li v-for="entry in topicEntries" :key="entry.id">
        <button
          type="button"
          class="legend-item"
          :class="{ 'legend-item-hidden': uiStore.hiddenCommunities.includes(entry.id) }"
          :aria-pressed="!uiStore.hiddenCommunities.includes(entry.id)"
          :disabled="uiStore.busy"
          @click="uiStore.toggleHiddenCommunity(entry.id)"
        >
          <span class="legend-item-label">{{ entry.label }}</span>
          <span
            class="legend-toggle"
            :class="{ 'legend-toggle-off': uiStore.hiddenCommunities.includes(entry.id) }"
            :style="uiStore.hiddenCommunities.includes(entry.id) ? {} : { background: entry.bg, borderColor: entry.border }"
          >
            <span class="legend-toggle-knob" />
          </span>
        </button>
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

const TYPE_ENTRIES = [
    { value: 'Tool', label: 'Tool' },
    { value: 'Database', label: 'Database' },
    { value: 'Publication', label: 'Publication' }
]

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
            // Object.entries gives string keys — normalized back to a number so
            // uiStore.hiddenCommunities.includes(entry.id) matches node.properties.community
            // (Array#includes uses strict equality, unlike plain-object key lookups above).
            id: Number(id),
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

.legend-top-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 8px 0;
}

.legend-title {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--insolito-text-muted);
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

.legend-item {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 3px 4px;
    border: none;
    border-radius: 4px;
    background: none;
    font-size: 0.85rem;
    color: var(--insolito-text);
    text-align: left;
    cursor: pointer;
    opacity: 1;
    transition: opacity 0.15s ease;
}

.legend-item:hover {
    background: var(--insolito-bg-footer);
}

.legend-item-hidden {
    opacity: 0.4;
}

.legend-mode-btn:disabled,
.legend-collapse-btn:disabled,
.legend-item:disabled {
    cursor: not-allowed;
    opacity: 0.5;
}

.legend-empty {
    color: var(--insolito-text-muted);
    font-size: 0.82rem;
}


.legend-item-label {
    flex: 1;
}

/* An explicit switch, not just the row dimming on click — a whole clickable row
   with no visible control reads as plain text, not something to toggle. Colored
   with the same fill/border as the entry it controls so the switch itself already
   tells you what it turns on/off, on top of being an obvious toggle shape. */
.legend-toggle {
    flex-shrink: 0;
    width: 28px;
    height: 16px;
    box-sizing: border-box;
    border-radius: 8px;
    border-width: 2px;
    border-style: solid;
    position: relative;
    background: var(--insolito-border);
    border-color: var(--insolito-border);
    transition: background 0.15s ease, border-color 0.15s ease;
}

.legend-toggle-knob {
    position: absolute;
    top: 1px;
    left: 1px;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--insolito-bg);
    transition: left 0.15s ease;
}

.legend-toggle:not(.legend-toggle-off) .legend-toggle-knob {
    left: 13px;
}

.legend-toggle-tool {
    background: var(--insolito-node-primary);
    border-color: var(--insolito-primary);
}

.legend-toggle-database {
    background: var(--insolito-node-tertiary);
    border-color: var(--insolito-node-tertiary-dark);
}

.legend-toggle-publication {
    background: var(--insolito-node-secondary);
    border-color: var(--insolito-secondary-hover);
}

/* Comes after the type-specific rules above on purpose — same selector specificity,
   source order decides, and "hidden" always needs to win over the entry's own color. */
.legend-toggle-off {
    background: var(--insolito-bg-footer);
    border-color: var(--insolito-border);
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
