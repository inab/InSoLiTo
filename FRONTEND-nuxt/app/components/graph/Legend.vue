<template>
  <div class="graph-legend">
    <button
      class="legend-toggle"
      :aria-expanded="uiStore.legendOpen"
      @click="uiStore.toggleLegend()"
    >
      <span>Legend</span>
      <svg
        viewBox="0 0 24 24"
        class="legend-chevron"
        :class="{ 'legend-chevron-collapsed': !uiStore.legendOpen }"
      >
        <path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </button>

    <ul v-if="uiStore.legendOpen" class="legend-list">
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
  </div>
</template>

<script setup>
const uiStore = useUiStore()
</script>

<style scoped>
.graph-legend {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 18;
    width: 180px;
    box-sizing: border-box;
    background: var(--insolito-bg);
    border-radius: 8px;
    border-top: 4px solid var(--insolito-border);
    box-shadow: 0 6px 24px rgba(28, 43, 58, 0.24);
    overflow: hidden;
}

.legend-toggle {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 16px;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 600;
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
}

.legend-list li {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    color: var(--insolito-text);
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
