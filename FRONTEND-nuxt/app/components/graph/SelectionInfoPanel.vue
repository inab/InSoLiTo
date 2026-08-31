<template>
  <div ref="panelRef" class="selection-info-panel" :data-node-type="selection.kind === 'node' ? selection.type : null" :style="anchorStyle">
    <button class="selection-info-close" aria-label="Close panel" @click="$emit('close')">
      &times;
    </button>

    <template v-if="selection.kind === 'edge'">
      <p class="selection-info-type">Co-citation</p>
      <h3 class="selection-info-title">{{ sourceLabel }} ↔ {{ targetLabel }}</h3>
      <p class="selection-info-meta">{{ selection.weight }} co-citations total</p>

      <p v-if="loading" class="selection-info-meta">Loading year breakdown…</p>
      <p v-else-if="error" class="selection-info-meta selection-info-error">{{ error }}</p>
      <ul v-else-if="breakdown.length" class="edge-year-list">
        <li v-for="entry in breakdown" :key="entry.year">
          <span>{{ entry.year }}</span>
          <span>{{ entry.times }}</span>
        </li>
      </ul>
      <p v-else class="selection-info-meta">No per-year data.</p>
    </template>

    <template v-else-if="selection.type === 'Publication'">
      <p class="selection-info-type">Publication</p>
      <h3 class="selection-info-title">{{ selection.properties?.title || selection.label }}</h3>
      <p v-if="selection.properties?.year" class="selection-info-meta">{{ selection.properties.year }}</p>
      <p v-if="communityLabel" class="selection-info-meta selection-info-community">
        <span class="selection-info-community-dot" :style="{ background: communityColor.bg, borderColor: communityColor.border }" />
        {{ communityLabel }}
      </p>
      <div class="selection-info-links">
        <a
          v-if="selection.properties?.doi"
          :href="`https://doi.org/${selection.properties.doi}`"
          target="_blank"
          rel="noopener noreferrer"
        >DOI</a>
        <a
          v-if="selection.properties?.pmid"
          :href="`https://pubmed.ncbi.nlm.nih.gov/${selection.properties.pmid}/`"
          target="_blank"
          rel="noopener noreferrer"
        >PubMed</a>
      </div>
    </template>

    <template v-else>
      <p class="selection-info-type">{{ selection.type }}</p>
      <h3 class="selection-info-title">{{ selection.label }}</h3>
      <p v-if="communityLabel" class="selection-info-meta selection-info-community">
        <span class="selection-info-community-dot" :style="{ background: communityColor.bg, borderColor: communityColor.border }" />
        {{ communityLabel }}
      </p>
      <div class="selection-info-links">
        <a
          v-if="selection.properties?.label"
          :href="`https://openebench.bsc.es/tool/${selection.properties.label}`"
          target="_blank"
          rel="noopener noreferrer"
        >Webpage</a>
        <button
          v-if="!isAlreadySearched"
          type="button"
          class="selection-info-add-link"
          :disabled="uiStore.busy"
          @click="$emit('add-to-graph', { name: selection.label, kind: selection.type })"
        >
          + Add to search
        </button>
        <span v-else class="selection-info-already-searched">In active search</span>
      </div>
    </template>
  </div>
</template>

<script setup>
const props = defineProps({
    // { kind: 'node', id, label, type, properties } | { kind: 'edge', id, source, target, weight, properties }
    selection: { type: Object, required: true }
})
defineEmits(['close', 'add-to-graph'])

const graphStore = useGraphStore()
const uiStore = useUiStore()

// Tool/Database only (the template branch this guards never renders for Publication
// or edges) — hides the button once the node is already one of graphStore.searchTerms,
// since clicking it again would just be graphStore.addSearchTerm()'s silent no-op with
// no visible feedback near this panel (the toast for that lives in the sidebar, which
// can be far from a click-anchored panel).
const isAlreadySearched = computed(() => {
    if (props.selection.kind !== 'node') return false
    return graphStore.searchTerms.some((term) => term.name === props.selection.label && term.kind === props.selection.type)
})

function labelForId (id) {
    return graphStore.nodes.find((node) => String(node.id) === id)?.label ?? 'Unknown'
}

const sourceLabel = computed(() => props.selection.kind === 'edge' ? labelForId(props.selection.source) : null)
const targetLabel = computed(() => props.selection.kind === 'edge' ? labelForId(props.selection.target) : null)

const communityLabel = computed(() => {
    if (props.selection.kind !== 'node') return null
    const id = props.selection.properties?.community
    if (id === undefined || id === null) return null
    return communityTopicById[id] || `Cluster ${id}`
})

const communityColor = computed(() => getCommunityColor(props.selection.kind === 'node' ? props.selection.properties?.community : undefined))

const { fetchBreakdown, loading, error } = useEdgeYearBreakdown()
const breakdown = ref([])

// The panel stays mounted while the user clicks from one edge straight to another
// (only v-if="null" unmounts it), so a plain await could let a slower, stale request
// overwrite a faster, newer one — the token guard keeps only the latest response.
let latestRequestToken = 0

watch(() => props.selection, async (selection) => {
    breakdown.value = []
    if (selection?.kind !== 'edge') return
    const token = ++latestRequestToken
    try {
        const result = await fetchBreakdown({ sourceId: selection.source, targetId: selection.target })
        if (token === latestRequestToken) breakdown.value = result
    } catch {
        // error is already surfaced via the composable's `error` ref
    }
}, { immediate: true })

// Anchors the panel near the clicked node/edge instead of a fixed screen corner —
// a fixed corner went unnoticed in feedback since it could be far from what was
// just clicked. Position is set once, at click time, and doesn't track the node
// across pan/zoom (same "context menu" behavior a user would already expect).
// Below the mobile breakpoint the panel keeps its CSS-driven bottom bar instead
// (see the media query below) — anchoring near a touch point makes less sense
// when the finger just covered that spot.
const MOBILE_BREAKPOINT = 600
const ANCHOR_OFFSET = 16
const ANCHOR_MARGIN = 12

const panelRef = ref(null)
const anchorStyle = ref({})

function repositionPanel () {
    const pos = props.selection?.clickPosition
    if (!pos || !panelRef.value || window.innerWidth <= MOBILE_BREAKPOINT) {
        anchorStyle.value = {}
        return
    }
    const rect = panelRef.value.getBoundingClientRect()
    const maxLeft = Math.max(ANCHOR_MARGIN, window.innerWidth - rect.width - ANCHOR_MARGIN)
    const maxTop = Math.max(ANCHOR_MARGIN, window.innerHeight - rect.height - ANCHOR_MARGIN)
    anchorStyle.value = {
        left: `${Math.min(Math.max(pos.x + ANCHOR_OFFSET, ANCHOR_MARGIN), maxLeft)}px`,
        top: `${Math.min(Math.max(pos.y + ANCHOR_OFFSET, ANCHOR_MARGIN), maxTop)}px`,
        right: 'auto',
        bottom: 'auto'
    }
}

let resizeObserver = null
onMounted(() => {
    repositionPanel()
    resizeObserver = new ResizeObserver(repositionPanel)
    if (panelRef.value) resizeObserver.observe(panelRef.value)
    window.addEventListener('resize', repositionPanel)
})
onUnmounted(() => {
    resizeObserver?.disconnect()
    window.removeEventListener('resize', repositionPanel)
})

// selection itself changes on every click (new object), so a plain watch already
// fires whenever the anchor point should move — nextTick so panelRef reflects the
// new content's size before measuring.
watch(() => props.selection, () => nextTick(repositionPanel))
</script>

<style scoped>
.selection-info-panel {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 18;
    width: 260px;
    box-sizing: border-box;
    padding: 20px;
    background: var(--insolito-bg);
    border-radius: 8px;
    border-top: 4px solid var(--insolito-border);
    box-shadow: 0 6px 24px rgba(28, 43, 58, 0.24);
}

.selection-info-panel[data-node-type='Tool'] {
    border-top-color: var(--insolito-node-primary);
}

.selection-info-panel[data-node-type='Database'] {
    border-top-color: var(--insolito-node-tertiary);
}

.selection-info-panel[data-node-type='Publication'] {
    border-top-color: var(--insolito-node-secondary);
}

@media (max-width: 600px) {
    .selection-info-panel {
        /* Anchored to the bottom, so it never needs to clear the top toggle button */
        bottom: 16px;
        left: 16px;
        right: 16px;
        width: auto;
    }
}

.selection-info-close {
    position: absolute;
    top: 8px;
    right: 10px;
    border: none;
    background: none;
    font-size: 1.4rem;
    line-height: 1;
    color: var(--insolito-text-muted);
    cursor: pointer;
}

.selection-info-close:hover {
    color: var(--insolito-text);
}

.selection-info-type {
    margin: 0 0 4px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--insolito-text-muted);
}

.selection-info-title {
    margin: 0 0 6px;
    font-size: 1.05rem;
    color: var(--insolito-text);
}

.selection-info-meta {
    margin: 0 0 12px;
    font-size: 0.85rem;
    color: var(--insolito-text-muted);
}

.selection-info-error {
    color: var(--insolito-danger);
}

.selection-info-community {
    display: flex;
    align-items: center;
    gap: 6px;
}

.selection-info-community-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
    box-sizing: border-box;
    border-width: 2px;
    border-style: solid;
}

.selection-info-links {
    display: flex;
    gap: 12px;
    margin-top: 12px;
}

.selection-info-links a {
    font-size: 0.9rem;
    font-weight: 600;
}

.selection-info-add-link {
    border: none;
    background: none;
    padding: 0;
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--insolito-primary);
    cursor: pointer;
}

.selection-info-add-link:hover:not(:disabled) {
    text-decoration: underline;
}

.selection-info-add-link:disabled {
    cursor: not-allowed;
    opacity: 0.5;
}

.selection-info-already-searched {
    font-size: 0.9rem;
    color: var(--insolito-text-muted);
}

.edge-year-list {
    list-style: none;
    margin: 0;
    padding: 0;
    max-height: 160px;
    overflow-y: auto;
}

.edge-year-list li {
    display: flex;
    justify-content: space-between;
    padding: 4px 0;
    font-size: 0.85rem;
    color: var(--insolito-text);
    border-bottom: 1px solid var(--insolito-border);
}

.edge-year-list li:last-child {
    border-bottom: none;
}
</style>
