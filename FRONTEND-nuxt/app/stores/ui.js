export const useUiStore = defineStore('ui', () => {
    const sidebarOpen = ref(false)
    const legendOpen = ref(false)
    // 'type' colors nodes by Tool/Database/Publication; 'topic' colors them by
    // their Louvain community (shared with Network.vue and Legend.vue).
    const colorMode = ref('type')
    // Independent per colorMode: hiding a type in 'type' mode doesn't affect what's
    // hidden when switching to 'topic' mode, and vice versa.
    const hiddenTypes = ref([])
    const hiddenCommunities = ref([])
    // True while Sidebar's rebuildGraph() has an in-flight request — read by
    // Screen.vue too, to show a loading indicator over the canvas.
    const rebuilding = ref(false)
    // Which part of rebuildGraph() is running, so Screen.vue's overlay text can be
    // accurate: 'searching' during the Neo4j request, 'building' once results are
    // in and Cytoscape is computing the layout. Only meaningful while rebuilding is true.
    const rebuildPhase = ref('searching')
    // True only right after Screen.vue mounts with an already-populated graph (i.e.
    // returning from the landing page via "Explore") — cleared once GraphNetwork's
    // initial layout settles. Combined with `rebuilding` below into `busy`, since the
    // sidebar/legend should be just as unusable during a restore as during a search.
    const restoringGraph = ref(false)
    // Single flag every sidebar/legend control disables against — true while either
    // a search or a graph restore is in flight.
    const busy = computed(() => rebuilding.value || restoringGraph.value)

    function setRebuilding (value) {
        rebuilding.value = value
    }

    function setRebuildPhase (phase) {
        rebuildPhase.value = phase
    }

    function setRestoringGraph (value) {
        restoringGraph.value = value
    }

    function toggleSidebar () {
        sidebarOpen.value = !sidebarOpen.value
    }

    function setSidebarOpen (open) {
        sidebarOpen.value = open
    }

    function toggleLegend () {
        legendOpen.value = !legendOpen.value
    }

    function setColorMode (mode) {
        colorMode.value = mode
    }

    function toggleHiddenType (type) {
        hiddenTypes.value = hiddenTypes.value.includes(type)
            ? hiddenTypes.value.filter((t) => t !== type)
            : [...hiddenTypes.value, type]
    }

    function toggleHiddenCommunity (id) {
        hiddenCommunities.value = hiddenCommunities.value.includes(id)
            ? hiddenCommunities.value.filter((c) => c !== id)
            : [...hiddenCommunities.value, id]
    }

    function resetLayers () {
        hiddenTypes.value = []
        hiddenCommunities.value = []
    }

    return {
        sidebarOpen,
        toggleSidebar,
        setSidebarOpen,
        legendOpen,
        toggleLegend,
        colorMode,
        setColorMode,
        hiddenTypes,
        hiddenCommunities,
        toggleHiddenType,
        toggleHiddenCommunity,
        resetLayers,
        rebuilding,
        setRebuilding,
        rebuildPhase,
        setRebuildPhase,
        restoringGraph,
        setRestoringGraph,
        busy
    }
})
