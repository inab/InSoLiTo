// Must match Sidebar.vue's OCCURRENCE_DEFAULT — the slider's visual default is
// meaningless if this store (what the query actually uses) doesn't start there too.
const OCCURRENCE_DEFAULT = 11

export const useFilterStore = defineStore('filter', () => {
    // null means "no filter" (matches the METAOCCUR_ALL query variant, no year condition).
    // occurrenceMin doesn't get the same "no filter" treatment: unlike year, most
    // co-citation edges are weak (times 2-4), so an unfiltered first search on a hub
    // tool fetches and lays out a huge, mostly-noise neighbourhood — it always starts
    // at OCCURRENCE_DEFAULT instead.
    const yearMin = ref(null)
    const yearMax = ref(null)
    const occurrenceMin = ref(OCCURRENCE_DEFAULT)

    function setFilters (newYearMin, newYearMax, newOccurrenceMin) {
        yearMin.value = newYearMin
        yearMax.value = newYearMax
        occurrenceMin.value = newOccurrenceMin
    }

    function reset () {
        yearMin.value = null
        yearMax.value = null
        occurrenceMin.value = OCCURRENCE_DEFAULT
    }

    return { yearMin, yearMax, occurrenceMin, setFilters, reset }
})
