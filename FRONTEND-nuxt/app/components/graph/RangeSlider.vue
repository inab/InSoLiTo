<template>
  <div ref="trackRef" class="range-slider" @pointerdown="onTrackPointerDown">
    <div class="range-slider-fill" :style="fillStyle" />
    <button
      v-for="(percent, i) in thumbPercents"
      :key="i"
      type="button"
      class="range-slider-thumb"
      :style="{ left: percent + '%' }"
      role="slider"
      aria-orientation="horizontal"
      :aria-valuemin="min"
      :aria-valuemax="max"
      :aria-valuenow="values[i]"
      tabindex="0"
      @pointerdown.stop="startDrag(i, $event)"
      @keydown="onKeydown(i, $event)"
    />
  </div>
</template>

<script setup>
const props = defineProps({
    min: { type: Number, required: true },
    max: { type: Number, required: true },
    modelValue: { type: [Number, Array], required: true },
    step: { type: Number, default: 1 },
    // Optional non-linear mapping (e.g. log scale). Both default to linear over [min, max].
    toPercent: { type: Function, default: null },
    fromPercent: { type: Function, default: null }
})
const emit = defineEmits(['update:modelValue', 'change'])

const isRange = computed(() => Array.isArray(props.modelValue))
const values = computed(() => (isRange.value ? props.modelValue : [props.modelValue]))

const valueToPercent = (value) => (props.toPercent
    ? props.toPercent(value)
    : ((value - props.min) / (props.max - props.min)) * 100)

const percentToValue = (percent) => {
    const raw = props.fromPercent
        ? props.fromPercent(percent)
        : props.min + (percent / 100) * (props.max - props.min)
    const stepped = Math.round(raw / props.step) * props.step
    return Math.min(props.max, Math.max(props.min, stepped))
}

const thumbPercents = computed(() => values.value.map(valueToPercent))

const fillStyle = computed(() => {
    if (isRange.value) {
        const [lo, hi] = thumbPercents.value
        return { left: lo + '%', width: Math.max(0, hi - lo) + '%' }
    }
    return { left: '0%', width: thumbPercents.value[0] + '%' }
})

const trackRef = ref(null)

function percentFromEvent (event) {
    const rect = trackRef.value.getBoundingClientRect()
    const raw = ((event.clientX - rect.left) / rect.width) * 100
    return Math.min(100, Math.max(0, raw))
}

function clampToNeighbours (index, value) {
    if (!isRange.value) return value
    if (index === 0) return Math.min(value, values.value[1])
    return Math.max(value, values.value[0])
}

function emitValues (nextValues, eventName) {
    emit(eventName, isRange.value ? nextValues : nextValues[0])
}

function applyToIndex (index, value) {
    const next = [...values.value]
    next[index] = clampToNeighbours(index, value)
    return next
}

let dragIndex = null

function startDrag (index, event) {
    dragIndex = index
    event.target.setPointerCapture(event.pointerId)
    window.addEventListener('pointermove', onDrag)
    window.addEventListener('pointerup', stopDrag)
}

function onDrag (event) {
    if (dragIndex === null) return
    const value = percentToValue(percentFromEvent(event))
    emitValues(applyToIndex(dragIndex, value), 'update:modelValue')
}

function stopDrag () {
    if (dragIndex === null) return
    dragIndex = null
    window.removeEventListener('pointermove', onDrag)
    window.removeEventListener('pointerup', stopDrag)
    emitValues(values.value, 'change')
}

function onTrackPointerDown (event) {
    const percent = percentFromEvent(event)
    const distances = values.value.map((v) => Math.abs(valueToPercent(v) - percent))
    const index = distances.length > 1 && distances[1] < distances[0] ? 1 : 0
    const value = percentToValue(percent)
    const next = applyToIndex(index, value)
    emitValues(next, 'update:modelValue')
    emitValues(next, 'change')
}

function onKeydown (index, event) {
    let delta = 0
    if (event.key === 'ArrowRight' || event.key === 'ArrowUp') delta = props.step
    else if (event.key === 'ArrowLeft' || event.key === 'ArrowDown') delta = -props.step
    else if (event.key === 'Home') { commitValue(index, props.min); return }
    else if (event.key === 'End') { commitValue(index, props.max); return }
    else return
    event.preventDefault()
    commitValue(index, values.value[index] + delta)
}

function commitValue (index, rawValue) {
    const value = Math.min(props.max, Math.max(props.min, rawValue))
    const next = applyToIndex(index, value)
    emitValues(next, 'update:modelValue')
    emitValues(next, 'change')
}
</script>

<style scoped>
.range-slider {
    position: relative;
    height: 20px;
    display: flex;
    align-items: center;
    cursor: pointer;
    touch-action: none;
}

.range-slider::before {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    height: 4px;
    border-radius: 2px;
    background: var(--insolito-border);
}

.range-slider-fill {
    position: absolute;
    height: 4px;
    border-radius: 2px;
    background: var(--insolito-primary);
}

.range-slider-thumb {
    position: absolute;
    top: 50%;
    width: 16px;
    height: 16px;
    margin-left: -8px;
    transform: translateY(-50%);
    border-radius: 50%;
    background: var(--insolito-bg);
    border: 2px solid var(--insolito-primary);
    box-shadow: 0 1px 4px rgba(28, 43, 58, 0.25);
    cursor: grab;
    padding: 0;
}

.range-slider-thumb:active {
    cursor: grabbing;
}

.range-slider-thumb:focus-visible {
    outline: 2px solid var(--insolito-secondary);
    outline-offset: 2px;
}
</style>
