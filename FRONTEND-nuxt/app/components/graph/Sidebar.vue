<template>
  <aside class="graph-sidebar" :class="open ? 'graph-sidebar-open' : 'graph-sidebar-closed'">
    <button type="button" class="graph-sidebar-logo-btn" aria-label="Back to home" @click="$emit('go-home')">
      <img src="~/assets/images/logo_InSoLiTo.png" alt="InSoLiTo Logo" class="graph-sidebar-logo">
    </button>

    <BButton class="graph-sidebar-reset" :disabled="uiStore.busy" @click="onReset">
      Reset
    </BButton>

    <section class="graph-sidebar-search">
      <h3 class="graph-sidebar-filter-title">Search</h3>
      <div class="graph-sidebar-search-input-wrap">
        <input
          v-model="searchTerm"
          type="text"
          placeholder="blast, 1000Genomes, MEGA..."
          class="graph-sidebar-search-input"
          :disabled="uiStore.busy"
          autocomplete="off"
          @focus="showSuggestions = true"
          @blur="onInputBlur"
          @keydown="onKeydown"
        >
        <ul v-if="showSuggestions && suggestions.length" class="graph-sidebar-suggestions">
          <li
            v-for="(suggestion, index) in suggestions"
            :key="suggestion.name"
            class="graph-sidebar-suggestion"
            :class="{ 'graph-sidebar-suggestion-highlighted': index === highlightedIndex }"
            @mousedown.prevent="onSelectSuggestion(suggestion)"
            @mouseenter="highlightedIndex = index"
          >
            <span class="graph-sidebar-suggestion-name">{{ suggestion.name }}</span>
            <span class="graph-sidebar-suggestion-kind">{{ suggestion.kind }}</span>
          </li>
        </ul>
        <p v-else-if="showSuggestions && searchTerm.trim()" class="graph-sidebar-suggestions-empty">
          No matches
        </p>
      </div>
      <BButton
        class="graph-sidebar-search-btn"
        :class="{ 'graph-sidebar-search-btn-stale': filtersStale }"
        :disabled="uiStore.busy || (!searchTerm.trim() && graphStore.searchTerms.length === 0)"
        :title="filtersStale ? 'Filters changed — click Search to update the graph' : undefined"
        @click="onSearchClick"
      >
        {{ uiStore.rebuilding ? 'Searching…' : 'Search' }}<span v-if="filtersStale && !uiStore.rebuilding" aria-hidden="true"> ⚠</span>
      </BButton>
      <div v-if="searchError || connectionError || searchNotice || emptyResultTerms.length" class="graph-toast-stack">
        <p v-if="searchError" class="graph-toast graph-toast-warning">{{ searchError }}</p>
        <p v-if="connectionError" class="graph-toast graph-toast-error">{{ connectionError }}</p>
        <p v-if="searchNotice" class="graph-toast">{{ searchNotice }}</p>
        <p v-if="emptyResultTerms.length" class="graph-toast">
          No results for {{ emptyResultTerms.map((name) => `"${name}"`).join(', ') }} with the current filters.
        </p>
      </div>
    </section>

    <section class="graph-sidebar-filter">
      <h3 class="graph-sidebar-filter-title">Publication year</h3>
      <GraphHistogram :values="yearCounts" />
      <GraphRangeSlider
        v-model="yearRange"
        :min="yearDomainMin"
        :max="yearDomainMax"
        :disabled="uiStore.busy"
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
        :disabled="uiStore.busy"
        @change="onOccurrenceChange"
      />
      <p class="graph-sidebar-filter-value">{{ occurrenceValue }}</p>
    </section>

    <section v-if="graphStore.searchTerms.length" class="graph-sidebar-active-searches">
      <h3 class="graph-sidebar-filter-title">Active searches</h3>
      <div v-for="group in groupedSearchTerms" :key="group.kind" class="graph-sidebar-search-group">
        <h4 class="graph-sidebar-search-group-title">
          <span class="graph-sidebar-search-term-dot" :class="`graph-sidebar-search-term-dot-${group.kind.toLowerCase()}`" />
          {{ group.label }}
        </h4>
        <ul class="graph-sidebar-search-terms">
          <li
            v-for="term in group.terms"
            :key="`${term.kind}-${term.name}`"
            class="graph-sidebar-search-term"
          >
            <span class="graph-sidebar-search-term-name">{{ term.name }}</span>
            <button
              type="button"
              class="graph-sidebar-search-term-remove"
              :aria-label="`Remove ${term.name}`"
              :disabled="uiStore.busy"
              @click="onRemoveSearchTerm(term)"
            >
              ×
            </button>
          </li>
        </ul>
      </div>
    </section>

    <section v-if="graphStore.nodes.length" class="graph-sidebar-export">
      <h3 class="graph-sidebar-filter-title">Export</h3>
      <div class="graph-sidebar-export-buttons">
        <BButton variant="outline-secondary" size="sm" :disabled="uiStore.busy" @click="$emit('export-png')">
          PNG
        </BButton>
        <BButton variant="outline-secondary" size="sm" :disabled="uiStore.busy" @click="onExportJson">
          JSON
        </BButton>
      </div>
    </section>
  </aside>
</template>

<script setup>
import YearData from '../../../../DB/YearSliderData.json'
import OccurData from '../../../../DB/RelationshipSliderData.json'

defineProps({
    open: { type: Boolean, default: true }
})
const emit = defineEmits(['reset', 'export-png', 'go-home'])

const filterStore = useFilterStore()
const graphStore = useGraphStore()
const uiStore = useUiStore()

const searchTerm = ref('')
const searchError = ref('')
// connectionError is separate from searchError: both are "problem" cards, but
// searchError is bad input (warning styling), connectionError is an actual
// request failure (error styling) — different severity, different accent color.
const connectionError = ref('')
// Informational feedback about the last completed action, distinct from the two
// above: searchNotice for "that term is already active", emptyResultTerms for the
// names of active terms whose query came back with zero nodes this rebuild.
// All four persist until the next action clears them, no auto-dismiss timer.
const searchNotice = ref('')
const emptyResultTerms = ref([])

const showSuggestions = ref(false)
const highlightedIndex = ref(-1)
const suggestions = computed(() => suggestSearchTerms(searchTerm.value))

// Snapshot of the year/occurrence values that produced the graph currently on
// screen — null until the first successful rebuild. filtersStale compares it
// against the live slider values so the Search button can flag "what you see
// doesn't match the filters anymore" instead of silently going out of sync.
const lastAppliedFilters = ref(null)
const filtersStale = computed(() => {
    if (!lastAppliedFilters.value) return false
    return lastAppliedFilters.value.yearMin !== yearRange.value[0] ||
        lastAppliedFilters.value.yearMax !== yearRange.value[1] ||
        lastAppliedFilters.value.occurrenceMin !== occurrenceValue.value
})

// Fixed order (not alphabetical by kind) so the groups don't reshuffle as you add/remove terms.
const SEARCH_GROUP_ORDER = [
    { kind: 'Tool', label: 'Tools' },
    { kind: 'Database', label: 'Databases' },
    { kind: 'Topic', label: 'Topics' }
]

const groupedSearchTerms = computed(() => SEARCH_GROUP_ORDER
    .map((group) => ({ ...group, terms: graphStore.searchTerms.filter((term) => term.kind === group.kind) }))
    .filter((group) => group.terms.length))

watch(searchTerm, () => {
    highlightedIndex.value = -1
})

function onInputBlur () {
    // Delayed so a click on a suggestion (mousedown, handled first) still registers
    // before the list disappears.
    setTimeout(() => { showSuggestions.value = false }, 150)
}

function onSelectSuggestion (suggestion) {
    searchTerm.value = suggestion.name
    showSuggestions.value = false
    highlightedIndex.value = -1
}

function onKeydown (event) {
    if (event.key === 'ArrowDown') {
        event.preventDefault()
        if (!suggestions.value.length) return
        showSuggestions.value = true
        highlightedIndex.value = Math.min(highlightedIndex.value + 1, suggestions.value.length - 1)
    } else if (event.key === 'ArrowUp') {
        event.preventDefault()
        highlightedIndex.value = Math.max(highlightedIndex.value - 1, -1)
    } else if (event.key === 'Escape') {
        showSuggestions.value = false
        highlightedIndex.value = -1
    } else if (event.key === 'Enter') {
        event.preventDefault()
        // A highlighted suggestion (arrow keys) just fills the input, same as
        // clicking it — Enter without one submits the search instead.
        const picked = suggestions.value[highlightedIndex.value]
        if (picked) {
            onSelectSuggestion(picked)
            return
        }
        showSuggestions.value = false
        onSearchClick()
    }
}

// Distinguishes why a search request failed, without leaking raw Cypher/HTTP
// details to the UI: 'database' is tagged explicitly by useNeo4jSearch when
// Neo4j itself reports a problem; anything with a response (an HTTP error
// status) is a server-side failure; anything else never got a response at all.
function classifySearchError (error) {
    if (error?.cause === 'database') return 'The database returned an error. Please try again.'
    if (error?.response || error?.statusCode || error?.status) return 'Server error. Please try again later.'
    return 'Connection failed. Please try again.'
}

// Shared by the Search button, Enter, and removing an "active search" entry —
// always re-derives the whole graph from graphStore.searchTerms + the current
// filters, rather than patching the existing nodes/edges in place. A node that's
// still reachable via another remaining term simply comes back from that term's
// own query; nothing needs manual pruning.
async function rebuildGraph () {
    if (!graphStore.searchTerms.length) {
        graphStore.clearResults()
        emptyResultTerms.value = []
        connectionError.value = ''
        return
    }
    uiStore.setRebuilding(true)
    uiStore.setRebuildPhase('searching')
    connectionError.value = ''
    emptyResultTerms.value = []
    try {
        // A fresh useNeo4jSearch() per term, not one shared instance, so each query's
        // loading/error refs don't race with the others running in parallel.
        const results = await Promise.all(graphStore.searchTerms.map((term) => useNeo4jSearch().search({
            name: term.name,
            kind: term.kind,
            occurrenceMin: filterStore.occurrenceMin,
            yearMin: filterStore.yearMin,
            yearMax: filterStore.yearMax
        })))
        uiStore.setRebuildPhase('building')
        graphStore.clearResults()
        results.forEach(({ nodes, edges, entryPointId }) => graphStore.addToGraph(nodes, edges, entryPointId))
        emptyResultTerms.value = graphStore.searchTerms
            .filter((_, index) => results[index].nodes.length === 0)
            .map((term) => term.name)
        lastAppliedFilters.value = { yearMin: yearRange.value[0], yearMax: yearRange.value[1], occurrenceMin: occurrenceValue.value }
        // rebuilding stays true here on purpose — Screen.vue clears it once GraphNetwork's
        // relayout for this new data actually finishes (see onNetworkReady), not right after
        // the fetch, so the sidebar doesn't re-enable while the layout is still computing.
    } catch (e) {
        connectionError.value = classifySearchError(e)
        uiStore.setRebuilding(false)
    }
}

async function onSearchClick () {
    searchError.value = ''
    searchNotice.value = ''
    const raw = searchTerm.value.trim()
    if (raw) {
        const resolved = resolveSearchTerm(raw)
        if (!resolved) {
            searchError.value = `No match found for "${raw}"`
            return
        }
        const added = graphStore.addSearchTerm(resolved)
        if (!added) {
            searchNotice.value = `"${resolved.name}" is already in your active searches.`
        }
        searchTerm.value = ''
    }
    await rebuildGraph()
}

async function onRemoveSearchTerm (term) {
    searchError.value = ''
    searchNotice.value = ''
    graphStore.removeSearchTerm(term)
    await rebuildGraph()
}

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

function onExportJson () {
    const visibility = { hiddenTypes: uiStore.hiddenTypes, hiddenCommunities: uiStore.hiddenCommunities, entryPointIds: graphStore.entryPointIds }
    const { nodes, edges } = filterVisibleGraph(graphStore.nodes, graphStore.edges, visibility)
    downloadGraphAsJson(nodes, edges)
}

function onReset () {
    yearRange.value = [yearDomainMin, yearDomainMax]
    occurrenceValue.value = occurrenceDomainMin
    searchTerm.value = ''
    searchError.value = ''
    connectionError.value = ''
    searchNotice.value = ''
    emptyResultTerms.value = []
    showSuggestions.value = false
    lastAppliedFilters.value = null
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
    overflow-y: auto;
    transition: transform 0.3s ease;
}

.graph-sidebar-open {
    transform: translateX(0);
}

.graph-sidebar-closed {
    transform: translateX(-100%);
}

.graph-sidebar-logo-btn {
    border: none;
    background: none;
    padding: 0;
    cursor: pointer;
    line-height: 0;
    opacity: 1;
    transition: opacity 0.15s ease;
}

.graph-sidebar-logo-btn:hover {
    opacity: 0.8;
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

.graph-sidebar-export {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.graph-sidebar-export-buttons {
    display: flex;
    gap: 8px;
}

.graph-sidebar-export-buttons .btn {
    flex: 1;
}

.graph-sidebar-filter,
.graph-sidebar-search {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.graph-sidebar-search-input {
    padding: 6px 10px;
    border: 1px solid var(--insolito-border);
    border-radius: 6px;
    font-size: 0.9rem;
    color: var(--insolito-text);
}

.graph-sidebar-search-input:focus {
    outline: none;
    border-color: var(--insolito-primary);
}

.graph-sidebar-search-input-wrap {
    position: relative;
    width: 100%;
}

.graph-sidebar-search-input-wrap .graph-sidebar-search-input {
    width: 100%;
    box-sizing: border-box;
}

.graph-sidebar-suggestions {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    right: 0;
    z-index: 22;
    margin: 0;
    padding: 4px 0;
    list-style: none;
    background: var(--insolito-bg);
    border: 1px solid var(--insolito-border);
    border-radius: 6px;
    box-shadow: 0 6px 20px rgba(28, 43, 58, 0.18);
    max-height: 220px;
    overflow-y: auto;
}

.graph-sidebar-suggestion {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 7px 10px;
    font-size: 0.85rem;
    cursor: pointer;
    border-left: 3px solid transparent;
}

.graph-sidebar-suggestion:hover,
.graph-sidebar-suggestion-highlighted {
    background: var(--insolito-bg-footer);
    border-left-color: var(--insolito-primary);
}

.graph-sidebar-suggestion-name {
    color: var(--insolito-text);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.graph-sidebar-suggestion-kind {
    flex-shrink: 0;
    padding: 2px 6px;
    border-radius: 4px;
    background: var(--insolito-bg-footer);
    color: var(--insolito-text-muted);
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

.graph-sidebar-suggestion-highlighted .graph-sidebar-suggestion-kind {
    background: var(--insolito-bg);
}

.graph-sidebar-suggestions-empty {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    right: 0;
    z-index: 22;
    margin: 0;
    padding: 6px 10px;
    font-size: 0.82rem;
    color: var(--insolito-text-muted);
    background: var(--insolito-bg);
    border: 1px solid var(--insolito-border);
    border-radius: 6px;
    box-shadow: 0 6px 20px rgba(28, 43, 58, 0.18);
}

.graph-toast-stack {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.graph-toast {
    margin: 0;
    padding: 8px 10px;
    border-radius: 6px;
    background: var(--insolito-bg-footer);
    color: var(--insolito-text-muted);
    font-size: 0.8rem;
}

/* Same shape, different fill: neutral info (default, no color) / warning (bad
   input, nothing broken) / error (something actually failed — connection,
   server, DB). Tints are rgba of the existing --insolito-secondary/-danger
   tokens, same exception already used for shadows elsewhere in this file. */
.graph-toast-warning {
    background: rgba(244, 124, 33, 0.12);
    color: var(--insolito-secondary-hover);
}

.graph-toast-error {
    background: rgba(192, 57, 43, 0.12);
    color: var(--insolito-danger);
}

.graph-sidebar-search-btn {
    width: 100%;
    background: var(--insolito-primary);
    border-color: var(--insolito-primary);
    border-radius: 6px;
    font-weight: 600;
}

.graph-sidebar-search-btn:hover {
    background: var(--insolito-primary-dark);
    border-color: var(--insolito-primary-dark);
}

.graph-sidebar-search-btn-stale {
    background: var(--insolito-secondary);
    border-color: var(--insolito-secondary);
}

.graph-sidebar-search-btn-stale:hover {
    background: var(--insolito-secondary-hover);
    border-color: var(--insolito-secondary-hover);
}

.graph-sidebar-active-searches {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.graph-sidebar-search-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.graph-sidebar-search-group-title {
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 0;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: var(--insolito-text-muted);
}

.graph-sidebar-search-terms {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.graph-sidebar-search-term {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 5px 8px;
    border-radius: 6px;
    background: var(--insolito-bg-footer);
}

.graph-sidebar-search-term-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
}

.graph-sidebar-search-term-dot-tool {
    background: var(--insolito-primary);
}

.graph-sidebar-search-term-dot-database {
    background: var(--insolito-node-tertiary);
}

.graph-sidebar-search-term-dot-topic {
    background: var(--insolito-secondary);
}

.graph-sidebar-search-term-name {
    flex: 1;
    font-size: 0.85rem;
    color: var(--insolito-text);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.graph-sidebar-search-term-remove {
    flex-shrink: 0;
    border: none;
    background: none;
    color: var(--insolito-text-muted);
    font-size: 1rem;
    line-height: 1;
    cursor: pointer;
    padding: 2px 4px;
}

.graph-sidebar-search-term-remove:hover {
    color: var(--insolito-danger);
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
