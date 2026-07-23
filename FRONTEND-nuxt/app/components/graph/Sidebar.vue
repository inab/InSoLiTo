<template>
  <aside class="graph-sidebar" :class="open ? 'graph-sidebar-open' : 'graph-sidebar-closed'">
    <img src="~/assets/images/logo_InSoLiTo.png" alt="InSoLiTo Logo" class="graph-sidebar-logo">

    <BButton class="graph-sidebar-reset" @click="onReset">
      Reset
    </BButton>

    <section class="graph-sidebar-filter">
      <h3 class="graph-sidebar-filter-title">Publication year</h3>
      <GraphHistogram :values="yearCounts" />
      <GraphRangeSlider
        v-model="yearRange"
        :min="yearDomainMin"
        :max="yearDomainMax"
        @change="onYearChange"
      />
      <p class="graph-sidebar-filter-value">{{ yearRange[0] }} – {{ yearRange[1] }}</p>
    </section>

    <section class="graph-sidebar-filter">
      <h3 class="graph-sidebar-filter-title">Minimum co-citations</h3>
      <GraphHistogram :values="occurrenceDensities" />
      <GraphRangeSlider
        v-model="occurrenceValue"
        :min="occurrenceDomainMin"
        :max="occurrenceDomainMax"
        :to-percent="occurrenceToPercent"
        :from-percent="occurrencePercentToValue"
        @change="onOccurrenceChange"
      />
      <p class="graph-sidebar-filter-value">{{ occurrenceValue }}</p>
    </section>

    <p class="graph-sidebar-placeholder">
      Search and legend will appear here.
    </p>
  </aside>
</template>

<script setup>
import YearData from '../../../../DB/YearSliderData.json'
import OccurData from '../../../../DB/RelationshipSliderData.json'

defineProps({
    open: { type: Boolean, default: true }
})
const emit = defineEmits(['reset'])

const filterStore = useFilterStore()

// Publication year: linear domain, taken straight from the year -> count map.
const yearEntries = Object.entries(YearData).map(([year, count]) => [Number(year), count]).sort((a, b) => a[0] - b[0])
const yearDomainMin = yearEntries[0][0]
const yearDomainMax = yearEntries[yearEntries.length - 1][0]
const yearCounts = yearEntries.map(([, count]) => count)
const yearRange = ref([yearDomainMin, yearDomainMax])

function onYearChange () {
    filterStore.setFilters(yearRange.value[0], yearRange.value[1], occurrenceValue.value)
}

// Minimum co-citations: log-scaled domain (occurrence counts span 2..~14000,
// most edges cluster at the low end) — same shape as the old logslider(), but
// bidirectional so the thumb can be positioned from a stored value, not just read from one.
const occurrenceEntries = Object.entries(OccurData).map(([times, density]) => [Number(times), density]).sort((a, b) => a[0] - b[0])
const occurrenceDomainMin = occurrenceEntries[0][0]
const occurrenceDomainMax = occurrenceEntries[occurrenceEntries.length - 1][0]
const occurrenceDensities = occurrenceEntries.map(([, density]) => density)
const occurrenceLogMin = Math.log(occurrenceDomainMin)
const occurrenceLogMax = Math.log(occurrenceDomainMax)
const occurrenceToPercent = (value) => ((Math.log(value) - occurrenceLogMin) / (occurrenceLogMax - occurrenceLogMin)) * 100
const occurrencePercentToValue = (percent) => Math.round(Math.exp(occurrenceLogMin + (percent / 100) * (occurrenceLogMax - occurrenceLogMin)))
const occurrenceValue = ref(occurrenceDomainMin)

function onOccurrenceChange () {
    filterStore.setFilters(yearRange.value[0], yearRange.value[1], occurrenceValue.value)
}

function onReset () {
    yearRange.value = [yearDomainMin, yearDomainMax]
    occurrenceValue.value = occurrenceDomainMin
    filterStore.reset()
    emit('reset')
}
</script>

<style scoped>
.graph-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100%;
    width: var(--graph-sidebar-width, 300px);
    z-index: 20;
    box-sizing: border-box;
    padding: 24px 20px;
    background: var(--insolito-bg);
    box-shadow: 4px 0 20px rgba(28, 43, 58, 0.18);
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
    transition: transform 0.3s ease;
}

.graph-sidebar-open {
    transform: translateX(0);
}

.graph-sidebar-closed {
    transform: translateX(-100%);
}

.graph-sidebar-logo {
    width: 160px;
}

.graph-sidebar-reset {
    background: var(--insolito-primary);
    border-color: var(--insolito-primary);
    border-radius: 6px;
    font-weight: 600;
    padding: 10px 24px;
}

.graph-sidebar-reset:hover {
    background: var(--insolito-primary-dark);
    border-color: var(--insolito-primary-dark);
}

.graph-sidebar-placeholder {
    color: var(--insolito-text-muted);
    font-size: 0.9rem;
    line-height: 1.5;
}

.graph-sidebar-filter {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.graph-sidebar-filter-title {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--insolito-text-muted);
    margin: 0;
}

.graph-sidebar-filter-value {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--insolito-text);
    margin: 0;
}
</style>
