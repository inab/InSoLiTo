<template>
  <BModal
    :model-value="modelValue"
    title="Import this graph?"
    centered
    ok-title="Import"
    cancel-title="Cancel"
    @ok="$emit('confirm')"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <p v-if="replacesExisting" class="import-confirm-warning">This will replace your current graph.</p>

    <p class="import-confirm-label">Search terms</p>
    <ul class="import-confirm-terms">
      <li v-for="term in searchTerms" :key="`${term.kind}-${term.name}`">
        <span class="import-confirm-term-name">{{ term.name }}</span>
        <span class="import-confirm-term-kind">{{ term.kind }}</span>
      </li>
    </ul>

    <p class="import-confirm-label">Filters</p>
    <p class="import-confirm-filters">{{ yearLabel }} · Minimum co-citations: {{ filters?.occurrenceMin }}</p>
  </BModal>
</template>

<script setup>
const props = defineProps({
    modelValue: { type: Boolean, default: false },
    searchTerms: { type: Array, default: () => [] },
    filters: { type: Object, default: null },
    replacesExisting: { type: Boolean, default: false }
})
defineEmits(['update:modelValue', 'confirm'])

const yearLabel = computed(() => {
    if (!props.filters) return ''
    return props.filters.yearMin != null && props.filters.yearMax != null
        ? `${props.filters.yearMin}–${props.filters.yearMax}`
        : 'All years'
})
</script>

<style scoped>
.import-confirm-warning {
    padding: 8px 10px;
    border-radius: 6px;
    background: rgba(244, 124, 33, 0.12);
    color: var(--insolito-secondary-hover);
    font-size: 0.85rem;
}

.import-confirm-label {
    margin: 0 0 6px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--insolito-text-muted);
}

.import-confirm-terms {
    list-style: none;
    margin: 0 0 16px;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.import-confirm-terms li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 5px 8px;
    border-radius: 6px;
    background: var(--insolito-bg-footer);
}

.import-confirm-term-name {
    font-size: 0.85rem;
    color: var(--insolito-text);
}

.import-confirm-term-kind {
    flex-shrink: 0;
    padding: 2px 6px;
    border-radius: 4px;
    background: var(--insolito-bg);
    color: var(--insolito-text-muted);
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

.import-confirm-filters {
    margin: 0;
    font-size: 0.85rem;
    color: var(--insolito-text);
}
</style>
