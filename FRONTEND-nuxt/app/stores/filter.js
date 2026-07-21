export const useFilterStore = defineStore('filter', () => {
    // null means "no filter" (matches the METAOCCUR_ALL query variant, no year/occurrence condition)
    const yearMin = ref(null)
    const yearMax = ref(null)
    const occurrenceMin = ref(null)

    function setFilters (newYearMin, newYearMax, newOccurrenceMin) {
        yearMin.value = newYearMin
        yearMax.value = newYearMax
        occurrenceMin.value = newOccurrenceMin
    }

    function reset () {
        yearMin.value = null
        yearMax.value = null
        occurrenceMin.value = null
    }

    return { yearMin, yearMax, occurrenceMin, setFilters, reset }
})
