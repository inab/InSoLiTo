<template>
  <BModal
    :model-value="modelValue"
    :title="title"
    centered
    ok-title="Download"
    cancel-title="Cancel"
    @ok="$emit('confirm')"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <p class="export-confirm-message">{{ message }}</p>
  </BModal>
</template>

<script setup>
defineProps({
    modelValue: { type: Boolean, default: false },
    title: { type: String, default: '' },
    message: { type: String, default: '' }
})
defineEmits(['update:modelValue', 'confirm'])
</script>

<style scoped>
.export-confirm-message {
    margin: 0;
    color: var(--insolito-text);
}
</style>
