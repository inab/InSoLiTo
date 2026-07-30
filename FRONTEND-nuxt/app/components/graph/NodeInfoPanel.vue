<template>
  <div class="node-info-panel" :data-node-type="node.type">
    <button class="node-info-close" aria-label="Close panel" @click="$emit('close')">
      &times;
    </button>

    <template v-if="node.type === 'Publication'">
      <p class="node-info-type">Publication</p>
      <h3 class="node-info-title">{{ node.properties?.title || node.label }}</h3>
      <p v-if="node.properties?.year" class="node-info-meta">{{ node.properties.year }}</p>
      <p v-if="communityLabel" class="node-info-meta node-info-community">
        <span class="node-info-community-dot" :style="{ background: communityColor.bg, borderColor: communityColor.border }" />
        {{ communityLabel }}
      </p>
      <div class="node-info-links">
        <a
          v-if="node.properties?.doi"
          :href="`https://doi.org/${node.properties.doi}`"
          target="_blank"
          rel="noopener noreferrer"
        >DOI</a>
        <a
          v-if="node.properties?.pmid"
          :href="`https://pubmed.ncbi.nlm.nih.gov/${node.properties.pmid}/`"
          target="_blank"
          rel="noopener noreferrer"
        >PubMed</a>
      </div>
    </template>

    <template v-else>
      <p class="node-info-type">{{ node.type }}</p>
      <h3 class="node-info-title">{{ node.label }}</h3>
      <p v-if="communityLabel" class="node-info-meta node-info-community">
        <span class="node-info-community-dot" :style="{ background: communityColor.bg, borderColor: communityColor.border }" />
        {{ communityLabel }}
      </p>
      <div class="node-info-links">
        <a
          v-if="node.properties?.label"
          :href="`https://openebench.bsc.es/tool/${node.properties.label}`"
          target="_blank"
          rel="noopener noreferrer"
        >Webpage</a>
      </div>
    </template>
  </div>
</template>

<script setup>
const props = defineProps({
    // { id, label, type: 'Tool' | 'Database' | 'Publication', properties }
    node: { type: Object, required: true }
})
defineEmits(['close'])

const communityLabel = computed(() => {
    const id = props.node.properties?.community
    if (id === undefined || id === null) return null
    return communityTopicById[id] || `Cluster ${id}`
})

const communityColor = computed(() => getCommunityColor(props.node.properties?.community))
</script>

<style scoped>
.node-info-panel {
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

.node-info-panel[data-node-type='Tool'] {
    border-top-color: var(--insolito-node-primary);
}

.node-info-panel[data-node-type='Database'] {
    border-top-color: var(--insolito-node-tertiary);
}

.node-info-panel[data-node-type='Publication'] {
    border-top-color: var(--insolito-node-secondary);
}

@media (max-width: 600px) {
    .node-info-panel {
        /* Anchored to the bottom, so it never needs to clear the top toggle button */
        bottom: 16px;
        left: 16px;
        right: 16px;
        width: auto;
    }
}

.node-info-close {
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

.node-info-close:hover {
    color: var(--insolito-text);
}

.node-info-type {
    margin: 0 0 4px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--insolito-text-muted);
}

.node-info-title {
    margin: 0 0 6px;
    font-size: 1.05rem;
    color: var(--insolito-text);
}

.node-info-meta {
    margin: 0 0 12px;
    font-size: 0.85rem;
    color: var(--insolito-text-muted);
}

.node-info-community {
    display: flex;
    align-items: center;
    gap: 6px;
}

.node-info-community-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
    box-sizing: border-box;
    border-width: 2px;
    border-style: solid;
}

.node-info-links {
    display: flex;
    gap: 12px;
    margin-top: 12px;
}

.node-info-links a {
    font-size: 0.9rem;
    font-weight: 600;
}
</style>
