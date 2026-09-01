<template>
  <BModal
    :model-value="modelValue"
    title="Share this graph"
    centered
    ok-only
    ok-title="Close"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <p class="share-modal-message">Anyone who opens this link sees the same graph — same searches and filters.</p>
    <div class="share-modal-row">
      <input type="text" readonly class="share-modal-input" :value="url" @focus="$event.target.select()">
      <BButton size="sm" @click="onCopy">{{ copied ? 'Copied!' : 'Copy' }}</BButton>
    </div>
  </BModal>
</template>

<script setup>
const props = defineProps({
    modelValue: { type: Boolean, default: false },
    url: { type: String, default: '' }
})
defineEmits(['update:modelValue'])

const copied = ref(false)
let copiedTimeout = null

async function onCopy () {
    clearTimeout(copiedTimeout)
    try {
        await navigator.clipboard.writeText(props.url)
    } catch {
        // Clipboard access can fail (permissions, non-secure context) — the link
        // is still selectable/copyable by hand from the input above either way.
    }
    copied.value = true
    copiedTimeout = setTimeout(() => { copied.value = false }, 2000)
}
</script>

<style scoped>
.share-modal-message {
    color: var(--insolito-text);
}

.share-modal-row {
    display: flex;
    gap: 8px;
}

.share-modal-input {
    flex: 1;
    min-width: 0;
    padding: 6px 10px;
    border: 1px solid var(--insolito-border);
    border-radius: 6px;
    font-size: 0.85rem;
    color: var(--insolito-text-muted);
    background: var(--insolito-bg-footer);
}
</style>
