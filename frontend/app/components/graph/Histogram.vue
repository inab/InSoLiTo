<template>
  <div class="histogram" aria-hidden="true">
    <div
      v-for="(height, i) in bars"
      :key="i"
      class="histogram-bar"
      :style="{ height: height + '%' }"
    />
  </div>
</template>

<script setup>
const props = defineProps({
    values: { type: Array, required: true }
})

const bars = computed(() => {
    const max = Math.max(...props.values, 0)
    if (max === 0) return props.values.map(() => 0)
    return props.values.map((v) => (v / max) * 100)
})
</script>

<style scoped>
.histogram {
    display: flex;
    align-items: flex-end;
    gap: 1px;
    height: 32px;
}

.histogram-bar {
    flex: 1;
    min-width: 1px;
    min-height: 1px;
    background: var(--insolito-node-primary);
    border-radius: 1px 1px 0 0;
}
</style>
