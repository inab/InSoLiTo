<template>
  <aside class="graph-sidebar" :class="open ? 'graph-sidebar-open' : 'graph-sidebar-closed'">
    <button type="button" class="graph-sidebar-logo-btn" aria-label="Back to home" @click="$emit('go-home')">
      <img src="~/assets/images/logo_InSoLiTo.png" alt="InSoLiTo Logo" class="graph-sidebar-logo">
    </button>

    <section class="graph-sidebar-meta">
      <h3 class="graph-sidebar-filter-title">Help</h3>
      <div class="graph-sidebar-meta-buttons">
        <BButton variant="outline-secondary" size="sm" :disabled="uiStore.busy" @click="uiStore.setAboutOpen(true)">
          About
        </BButton>
        <BButton variant="outline-secondary" size="sm" :disabled="uiStore.busy" @click="uiStore.setHowToOpen(true)">
          How to use
        </BButton>
      </div>
    </section>

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
      <div class="graph-sidebar-search-row">
        <BButton
          class="graph-sidebar-search-btn"
          :class="{ 'graph-sidebar-search-btn-stale': filtersStale }"
          :disabled="uiStore.busy || (!searchTerm.trim() && graphStore.searchTerms.length === 0)"
          :title="filtersStale ? 'Filters changed — click Search to update the graph' : undefined"
          @click="onSearchClick"
        >
          {{ uiStore.rebuilding ? 'Searching…' : 'Search' }}<span v-if="filtersStale && !uiStore.rebuilding" aria-hidden="true"> ⚠</span>
        </BButton>
        <BButton class="graph-sidebar-reset" :disabled="uiStore.busy" @click="onReset">
          Reset
        </BButton>
      </div>
      <div v-if="searchError || uiStore.connectionError || searchNotice || emptyResultTerms.length" class="graph-toast-stack">
        <p v-if="searchError" class="graph-toast graph-toast-warning">{{ searchError }}</p>
        <p v-if="uiStore.connectionError" class="graph-toast graph-toast-error">{{ uiStore.connectionError }}</p>
        <p v-if="searchNotice" class="graph-toast">{{ searchNotice }}</p>
        <p v-if="emptyResultTerms.length" class="graph-toast">
          No results for {{ emptyResultTerms.map((name) => `"${name}"`).join(', ') }} with the current filters.
        </p>
      </div>
    </section>

    <section v-if="graphStore.searchTerms.length" class="graph-sidebar-active-searches">
      <h3 class="graph-sidebar-filter-title">Active search</h3>
      <p class="graph-sidebar-section-hint">Terms currently included in the graph.</p>
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

    <section class="graph-sidebar-filters">
      <h3 class="graph-sidebar-filter-title">Filters</h3>

      <div class="graph-sidebar-filter">
        <h4 class="graph-sidebar-filter-subtitle">Publication year</h4>
        <GraphHistogram :values="yearCounts" />
        <GraphRangeSlider
          v-model="yearRange"
          :min="yearDomainMin"
          :max="yearDomainMax"
          :disabled="uiStore.busy"
          @change="onYearChange"
        />
        <p class="graph-sidebar-filter-value">{{ yearRange[0] }} – {{ yearRange[1] }}</p>
      </div>

      <div class="graph-sidebar-filter">
        <h4 class="graph-sidebar-filter-subtitle">Minimum co-citations</h4>
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
      </div>

      <div v-if="toolTypeEntries.length" class="graph-sidebar-filter">
        <h4 class="graph-sidebar-filter-subtitle">Tool type</h4>
        <div class="graph-sidebar-tooltype-list">
          <label v-for="entry in toolTypeEntries" :key="entry.type" class="graph-sidebar-tooltype-item">
            <input
              type="checkbox"
              :checked="!uiStore.hiddenToolTypes.includes(entry.type)"
              :disabled="uiStore.busy"
              @change="uiStore.toggleHiddenToolType(entry.type)"
            >
            {{ entry.label }} ({{ entry.count }})
          </label>
        </div>
      </div>
    </section>

    <section class="graph-sidebar-import">
      <h3 class="graph-sidebar-filter-title">Import</h3>
      <label
        class="graph-sidebar-import-label"
        :class="{ 'graph-sidebar-import-label-disabled': uiStore.busy, 'graph-sidebar-import-label-dragover': importDragActive }"
        @dragover.prevent="onImportDragOver"
        @dragleave.prevent="onImportDragLeave"
        @drop.prevent="onImportDrop"
      >
        <input
          type="file"
          accept="application/json"
          class="graph-sidebar-import-input"
          :disabled="uiStore.busy"
          @change="onImportFileChange"
        >
        Choose or drop a JSON file…
      </label>
      <p v-if="uiStore.importError" class="graph-toast graph-toast-warning">{{ uiStore.importError }}</p>
    </section>

    <section v-if="graphStore.nodes.length" class="graph-sidebar-export">
      <h3 class="graph-sidebar-filter-title">Export</h3>
      <div class="graph-sidebar-export-buttons">
        <BButton variant="outline-secondary" size="sm" :disabled="uiStore.busy" @click="requestExport('png')">
          PNG
        </BButton>
        <BButton variant="outline-secondary" size="sm" :disabled="uiStore.busy" @click="requestExport('json')">
          JSON
        </BButton>
        <BButton variant="outline-secondary" size="sm" :disabled="uiStore.busy" @click="requestExport('csv')">
          CSV
        </BButton>
        <BButton variant="outline-secondary" size="sm" :disabled="uiStore.busy" @click="requestExport('graphml')">
          GraphML
        </BButton>
        <BButton variant="outline-secondary" size="sm" :disabled="uiStore.busy" @click="requestShare">
          Share
        </BButton>
      </div>
    </section>
  </aside>

  <GraphExportConfirmModal
    :model-value="!!exportConfirm"
    :title="exportConfirm?.title"
    :message="exportConfirm?.message"
    @update:model-value="(open) => { if (!open) exportConfirm = null }"
    @confirm="onExportConfirmed"
  />
  <GraphShareModal v-model="shareModalOpen" :url="shareUrl" />
  <GraphImportConfirmModal
    :model-value="!!importPreview"
    :search-terms="importPreview?.searchTerms ?? []"
    :filters="importPreview?.filters ?? null"
    :replaces-existing="graphStore.nodes.length > 0"
    @update:model-value="(open) => { if (!open) importPreview = null }"
    @confirm="onImportConfirmed"
  />
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
// connectionError lives in uiStore (not a local ref here) — both this toast and
// Screen.vue's canvas card read the same value. searchError is bad input (warning
// styling), connectionError is an actual request failure (error styling).
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
        uiStore.setConnectionError('')
        uiStore.setImportError('')
        // Defensive, not load-bearing for this function's other callers (none of
        // them set rebuilding=true before reaching this branch) — but restoreFromMetadata
        // below now does, to cover the file-reading step ahead of any search, and
        // needs this branch to still turn it back off if every imported term gets
        // skipped as unknown (searchTerms ends up empty).
        uiStore.setRebuilding(false)
        return
    }
    uiStore.setRebuilding(true)
    uiStore.setRebuildPhase('searching')
    uiStore.setConnectionError('')
    uiStore.setImportError('')
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
        uiStore.setConnectionError(classifySearchError(e))
        uiStore.setRebuilding(false)
    }
}

// Re-runs the current search terms unchanged — used by the canvas's connection-error
// card ("Try again"), which retries as-is rather than changing anything about the request.
async function retrySearch () {
    await rebuildGraph()
}

// Widens the year range to the full domain and puts the occurrence filter back at
// OCCURRENCE_DEFAULT (not occurrenceDomainMin) — used by the canvas's no-results card
// ("Reset filters"). Going all the way to the domain minimum would readmit the exact
// performance problem #181 fixed (a hub search like BLAST at occurrenceMin=2 nearly
// hangs the browser); the main Reset button doesn't go there either, and this
// shouldn't diverge from it just because it starts from the empty-results card.
// Unlike the main Reset button, this keeps the active search terms — it only
// loosens what's filtering them out.
async function resetFilters () {
    yearRange.value = [yearDomainMin, yearDomainMax]
    occurrenceValue.value = OCCURRENCE_DEFAULT
    filterStore.setFilters(null, null, OCCURRENCE_DEFAULT)
    await rebuildGraph()
}

// Adds one of the canvas's example chips (initial/reset state) as a real search term
// and runs it — same mechanism as typing a name and pressing Search.
async function runExampleSearch (term) {
    graphStore.addSearchTerm(term)
    await rebuildGraph()
}

// Triggered from the "Add to graph" button on a clicked node's info panel. The
// panel itself already hides that button once the node is an active search term
// (see SelectionInfoPanel's isAlreadySearched), so the duplicate branch here is
// only a safety net, not the primary way a user finds out.
async function addNodeToGraph (term) {
    searchError.value = ''
    searchNotice.value = ''
    const added = graphStore.addSearchTerm(term)
    if (!added) {
        searchNotice.value = `"${term.name}" is already in your active searches.`
        return
    }
    await rebuildGraph()
}

defineExpose({ retrySearch, resetFilters, runExampleSearch, addNodeToGraph, restoreFromMetadata })

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

// filterStore treats null as "no year filter" (the METAOCCUR_ALL query variant, one
// aggregate edge per pair). The slider always reports concrete numbers though, even
// at rest — so a range spanning the full domain (untouched, or dragged back out) has
// to be translated back to null here, or the query silently switches to METAOCCUR
// (one edge per year) despite the displayed range looking identical to "no filter".
function yearFilterValue (range) {
    if (range[0] === yearDomainMin && range[1] === yearDomainMax) return [null, null]
    return range
}

function onYearChange () {
    const [min, max] = yearFilterValue(yearRange.value)
    filterStore.setFilters(min, max, occurrenceValue.value)
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
// Defaults to 11, not the domain minimum (2) — most co-citation edges are weak
// (times 2-4), so starting at the true minimum makes a hub search like BLAST fetch
// and lay out a huge, mostly-noise neighbourhood. 11 matches the very first version
// of the app's default, and is still adjustable down to occurrenceDomainMin via the slider.
const OCCURRENCE_DEFAULT = 11
const occurrenceValue = ref(OCCURRENCE_DEFAULT)

function onOccurrenceChange () {
    const [min, max] = yearFilterValue(yearRange.value)
    filterStore.setFilters(min, max, occurrenceValue.value)
}

// Tool/Database only, and only the types actually present in the graph currently
// on screen (not the full static list of 15 OEB categories) — same "reflect what's
// actually here" approach as Legend.vue's topicEntries, since most searches only
// ever surface a handful of them.
const toolTypeEntries = computed(() => {
    const counts = {}
    graphStore.nodes.forEach((node) => {
        (node.properties?.toolType || []).forEach((type) => {
            counts[type] = (counts[type] || 0) + 1
        })
    })
    return Object.entries(counts)
        .map(([type, count]) => ({ type, count, label: formatToolType(type) }))
        .sort((a, b) => b.count - a.count)
})

// Shared by all four export formats so "what's currently hidden via the legend"
// (uiStore.hiddenTypes/hiddenCommunities) is excluded consistently — the PNG gets
// this for free (Cytoscape doesn't draw display:none elements), these don't.
function visibleGraph () {
    const visibility = { hiddenTypes: uiStore.hiddenTypes, hiddenCommunities: uiStore.hiddenCommunities, hiddenToolTypes: uiStore.hiddenToolTypes, entryPointIds: graphStore.entryPointIds }
    return filterVisibleGraph(graphStore.nodes, graphStore.edges, visibility)
}

function currentFilters () {
    return { yearMin: filterStore.yearMin, yearMax: filterStore.yearMax, occurrenceMin: filterStore.occurrenceMin }
}

function currentLayers () {
    return { hiddenTypes: uiStore.hiddenTypes, hiddenCommunities: uiStore.hiddenCommunities, hiddenToolTypes: uiStore.hiddenToolTypes }
}

// searchTerms + filters (what to search for and with what constraints) plus the
// Legend/Filters visibility layers (what to hide once it's drawn) — not the
// (possibly legend-trimmed) visible node/edge set itself, since what makes this
// file re-importable is being able to replay the same searches and re-apply the
// same hide/show state, not a record of which nodes happened to be shown when it
// was exported.
function currentState () {
    return { searchTerms: graphStore.searchTerms, filters: currentFilters(), layers: currentLayers() }
}

// Every export/share button opens a confirm-first popup instead of acting
// immediately, so nothing downloads (or gets copied for sharing) on a stray
// click. EXPORT_ACTIONS maps each format's button to its title/message/actual
// download call, so requestExport() and the modal in the template stay generic.
const EXPORT_ACTIONS = {
    png: {
        title: 'Download graph as PNG?',
        message: 'Downloads the current view of the graph as a PNG image.',
        run: () => emit('export-png')
    },
    json: {
        title: 'Download graph as JSON?',
        message: 'Downloads the graph together with its search terms and filters, so it can be re-imported later to recreate this exact graph.',
        run: () => {
            const { nodes, edges } = visibleGraph()
            downloadGraphAsJson(nodes, edges, buildStateMetadata(currentState()))
        }
    },
    csv: {
        title: 'Download graph as CSV?',
        message: 'Downloads the graph as a plain data file (nodes and edges), for opening in a spreadsheet.',
        run: () => {
            const { nodes, edges } = visibleGraph()
            downloadGraphAsCsv(nodes, edges, buildStateMetadata(currentState()))
        }
    },
    graphml: {
        title: 'Download graph as GraphML?',
        message: 'Downloads the graph in GraphML format, for opening in tools like Gephi or Cytoscape Desktop.',
        run: () => {
            const { nodes, edges } = visibleGraph()
            downloadGraphAsGraphml(nodes, edges, graphStore.searchTerms)
        }
    }
}

const exportConfirm = ref(null)

function requestExport (format) {
    exportConfirm.value = EXPORT_ACTIONS[format]
}

function onExportConfirmed () {
    exportConfirm.value?.run()
    exportConfirm.value = null
}

const shareUrl = ref('')
const shareModalOpen = ref(false)

function requestShare () {
    shareUrl.value = buildShareUrl(currentState())
    shareModalOpen.value = true
}

// Shared by file import and the share-link restore on app load (Screen.vue calls
// this via sidebarRef, same pattern as retrySearch/runExampleSearch/addNodeToGraph)
// — replays the saved searches through the normal pipeline instead of injecting
// nodes/edges directly, so the result is a live graph, not a frozen snapshot.
async function restoreFromMetadata ({ searchTerms: terms, filters, layers }) {
    // Resolve against the dataset first (same check the manual search box relies
    // on, resolveSearchTerm) — nothing in graphStore is touched yet. A hand-edited
    // or corrupted file can carry a name/kind pair that doesn't exist; catching
    // that here gives an immediate, specific message instead of a slower round
    // trip to Neo4j that would only ever say "zero results", indistinguishable
    // from a real term that's just filtered out by year/occurrence.
    const resolved = []
    const skipped = []
    terms.forEach((term) => {
        const match = resolveSearchTerm(term.name)
        if (match && match.kind === term.kind) {
            resolved.push(match)
        } else {
            skipped.push(term.name)
        }
    })

    // If every term is unknown, this is a hard failure, not a partial import —
    // bail out before touching the graph store at all, so whatever was already
    // on screen (and its own active searches) survives untouched instead of
    // getting cleared for a replacement that never arrives.
    if (!resolved.length) {
        uiStore.setImportError('None of the terms in that file exist in the current dataset.')
        return
    }

    // Both callers (onImportConfirmed below, and Screen.vue's share-link restore
    // on app load) reach this function with the loading overlay still off — set
    // here so it covers the whole clear+search span, not just once rebuildGraph()
    // reaches Neo4j. (handleImportFile's own 'reading' phase, for the file.text()
    // step, is already over by this point — it closes before the confirm popup
    // even opens.)
    uiStore.setRebuilding(true)
    uiStore.setRebuildPhase('searching')
    // Not graphStore.reset() — see clearSearchTerms()'s own comment for why nodes/
    // edges must stay untouched until rebuildGraph() replaces them atomically.
    graphStore.clearSearchTerms()
    searchError.value = ''
    searchNotice.value = ''
    emptyResultTerms.value = []
    uiStore.setConnectionError('')
    resolved.forEach((term) => graphStore.addSearchTerm(term))

    yearRange.value = filters.yearMin != null && filters.yearMax != null ? [filters.yearMin, filters.yearMax] : [yearDomainMin, yearDomainMax]
    occurrenceValue.value = filters.occurrenceMin ?? OCCURRENCE_DEFAULT
    filterStore.setFilters(filters.yearMin ?? null, filters.yearMax ?? null, filters.occurrenceMin ?? OCCURRENCE_DEFAULT)
    // A full replacement, not a merge with whatever was hidden before the import —
    // same reasoning as the graph itself only ever being replaced by a successful
    // import, never merged (see the comment on the "every term unknown" bail-out
    // above). layers is always normalized to concrete arrays by parseStateMetadata
    // by the time it reaches here, even for a file saved before this field existed.
    uiStore.setLayers(layers)
    // rebuildGraph() clears uiStore.importError at its own start (same spot it
    // clears connectionError) — so the "skipped" message has to be set *after* it
    // resolves, not before, or it would wipe itself out immediately.
    await rebuildGraph()
    if (skipped.length) {
        uiStore.setImportError(`Skipped unknown term${skipped.length > 1 ? 's' : ''}: ${skipped.join(', ')}`)
    }
}

const importPreview = ref(null)
const importDragActive = ref(false)

// Reads and validates the file, then opens the confirm-with-preview popup
// instead of acting immediately — same "nothing happens on a stray drop/click"
// principle already applied to the export/share buttons. restoreFromMetadata()
// (called from onImportConfirmed, below) is what actually replaces the graph;
// this function only ever reads and reports on the file.
async function handleImportFile (file) {
    if (!file) return
    uiStore.setImportError('')
    // 'reading' covers just this function's own file.text()/JSON.parse() step —
    // near-instant for a small file, but still worth a loading state since a
    // large one could take a moment. Set before await, so the overlay is already
    // up while the file is being read, not just once it's fully parsed.
    uiStore.setRebuilding(true)
    uiStore.setRebuildPhase('reading')

    let result
    try {
        result = parseStateMetadata(JSON.parse(await file.text()))
    } catch {
        uiStore.setRebuilding(false)
        uiStore.setImportError("Could not read that file — it isn't valid JSON.")
        return
    }
    uiStore.setRebuilding(false)

    if (!result.data) {
        uiStore.setImportError(result.error)
        return
    }
    importPreview.value = result.data
}

function onImportFileChange (event) {
    const file = event.target.files?.[0]
    event.target.value = ''
    handleImportFile(file)
}

function onImportDragOver () {
    if (uiStore.busy) return
    importDragActive.value = true
}

function onImportDragLeave () {
    importDragActive.value = false
}

function onImportDrop (event) {
    importDragActive.value = false
    if (uiStore.busy) return
    handleImportFile(event.dataTransfer?.files?.[0])
}

async function onImportConfirmed () {
    const data = importPreview.value
    importPreview.value = null
    if (data) await restoreFromMetadata(data)
}

function onReset () {
    yearRange.value = [yearDomainMin, yearDomainMax]
    occurrenceValue.value = OCCURRENCE_DEFAULT
    searchTerm.value = ''
    searchError.value = ''
    uiStore.setConnectionError('')
    searchNotice.value = ''
    emptyResultTerms.value = []
    exportConfirm.value = null
    shareModalOpen.value = false
    importPreview.value = null
    uiStore.setImportError('')
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
    gap: 24px;
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

.graph-sidebar-export {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.graph-sidebar-export-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.graph-sidebar-export-buttons .btn {
    flex: 1 1 70px;
}

.graph-sidebar-import {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.graph-sidebar-import-label {
    display: block;
    width: 100%;
    box-sizing: border-box;
    padding: 6px 10px;
    border: 1px dashed var(--insolito-border);
    border-radius: 6px;
    font-size: 0.85rem;
    color: var(--insolito-text-muted);
    text-align: center;
    cursor: pointer;
}

.graph-sidebar-import-label:hover {
    border-color: var(--insolito-primary);
    color: var(--insolito-text);
}

.graph-sidebar-import-label-dragover {
    border-color: var(--insolito-primary);
    border-style: solid;
    background: var(--insolito-bg-footer);
    color: var(--insolito-text);
}

.graph-sidebar-import-label-disabled {
    cursor: not-allowed;
    opacity: 0.5;
}

.graph-sidebar-import-input {
    /* Hidden but still keyboard/screen-reader reachable via the wrapping <label> —
       display:none would remove it from the accessibility tree entirely. */
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    opacity: 0;
}

.graph-sidebar-meta {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.graph-sidebar-meta-buttons {
    width: 100%;
    display: flex;
    gap: 8px;
}

.graph-sidebar-meta-buttons .btn {
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

.graph-sidebar-search-row {
    display: flex;
    width: 100%;
    gap: 8px;
}

.graph-sidebar-search-btn,
.graph-sidebar-reset {
    background: var(--insolito-primary);
    border-color: var(--insolito-primary);
    border-radius: 6px;
    font-weight: 600;
}

.graph-sidebar-search-btn:hover,
.graph-sidebar-reset:hover {
    background: var(--insolito-primary-dark);
    border-color: var(--insolito-primary-dark);
}

.graph-sidebar-search-btn {
    flex: 3;
}

.graph-sidebar-reset {
    flex: 1;
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
    gap: 8px;
}

.graph-sidebar-search-group-title {
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 0;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--insolito-text);
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
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--insolito-text-muted);
    margin: 0;
}

.graph-sidebar-section-hint {
    font-size: 0.78rem;
    color: var(--insolito-text-muted);
    margin: -4px 0 0;
}

.graph-sidebar-filters {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.graph-sidebar-filter-subtitle {
    margin: 0;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--insolito-text);
}

.graph-sidebar-filter-value {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--insolito-text);
    margin: 0;
}

.graph-sidebar-tooltype-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
    max-height: 160px;
    overflow-y: auto;
}

.graph-sidebar-tooltype-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    color: var(--insolito-text);
    cursor: pointer;
}

.graph-sidebar-tooltype-item input {
    accent-color: var(--insolito-primary);
    cursor: pointer;
}
</style>
