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
    // toolType (e.g. 'cmd', 'web', 'db') is a finer breakdown than hiddenTypes'
    // Tool/Database/Publication, only meaningful for Tool/Database nodes, and
    // independent of colorMode — it's a sidebar Filters control, not a Legend tab.
    // A node can carry several toolType values at once, so this hides it only once
    // NONE of them are still active (see isNodeHidden's "any active" semantics).
    const hiddenToolTypes = ref([])
    // True while Sidebar's rebuildGraph() has an in-flight request — read by
    // Screen.vue too, to show a loading indicator over the canvas.
    const rebuilding = ref(false)
    // Which part of the current graph-loading operation is running, so Screen.vue's
    // overlay text can be accurate: 'reading' while a JSON import is being read
    // off disk (Sidebar.vue's onImportFile, before there's even a search to run),
    // 'searching' during the Neo4j request, 'building' once results are in and
    // Cytoscape is computing the layout. Only meaningful while rebuilding is true.
    const rebuildPhase = ref('searching')
    // True only right after Screen.vue mounts with an already-populated graph (i.e.
    // returning from the landing page via "Explore") — cleared once GraphNetwork's
    // initial layout settles. Combined with `rebuilding` below into `busy`, since the
    // sidebar/legend should be just as unusable during a restore as during a search.
    const restoringGraph = ref(false)
    // Single flag every sidebar/legend control disables against — true while either
    // a search or a graph restore is in flight.
    const busy = computed(() => rebuilding.value || restoringGraph.value)
    // About modal is reachable from both the landing page (Hero's "About" button) and
    // the graph screen (Sidebar) — lives in uiStore, not local component state, so
    // both can open it. How-to-use is only ever opened from the graph screen, but kept
    // alongside it for consistency (same button row, same on/off pattern).
    const aboutOpen = ref(false)
    const howToOpen = ref(false)
    // Lives here (not local Sidebar.vue state) so Screen.vue can also read it and
    // show a dedicated error card on the canvas — the canvas placeholder used to
    // only check searchTerms.length, which showed a misleading "no results"
    // message when a search actually failed to reach the server.
    const connectionError = ref('')
    // Same reasoning as connectionError above, same lifecycle (cleared at the top
    // of Sidebar.vue's rebuildGraph(), so it survives exactly until the next real
    // search/import attempt) — a JSON import can fail before any request is even
    // made (bad syntax, wrong shape, no matching terms), which used to be a
    // sidebar-only message a user staring at the canvas could easily miss, and
    // that never went away on its own if they moved on to something else.
    const importError = ref('')

    function setRebuilding (value) {
        rebuilding.value = value
    }

    function setRebuildPhase (phase) {
        rebuildPhase.value = phase
    }

    function setRestoringGraph (value) {
        restoringGraph.value = value
    }

    function setAboutOpen (value) {
        aboutOpen.value = value
    }

    function setHowToOpen (value) {
        howToOpen.value = value
    }

    function setConnectionError (value) {
        connectionError.value = value
    }

    function setImportError (value) {
        importError.value = value
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

    function toggleHiddenToolType (type) {
        hiddenToolTypes.value = hiddenToolTypes.value.includes(type)
            ? hiddenToolTypes.value.filter((t) => t !== type)
            : [...hiddenToolTypes.value, type]
    }

    function resetLayers () {
        hiddenTypes.value = []
        hiddenCommunities.value = []
        hiddenToolTypes.value = []
    }

    // Used by Sidebar.vue's restoreFromMetadata (JSON import / Share link) to
    // replace all three layer-visibility arrays at once, rather than toggling one
    // at a time — the saved state is a full replacement, not a diff against
    // whatever happened to be hidden before the import. Falls back to "nothing
    // hidden" per array so a file saved before this field existed still restores
    // cleanly instead of leaving stale values in place.
    function setLayers (layers) {
        hiddenTypes.value = layers?.hiddenTypes ?? []
        hiddenCommunities.value = layers?.hiddenCommunities ?? []
        hiddenToolTypes.value = layers?.hiddenToolTypes ?? []
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
        hiddenToolTypes,
        toggleHiddenType,
        toggleHiddenCommunity,
        toggleHiddenToolType,
        resetLayers,
        setLayers,
        rebuilding,
        setRebuilding,
        rebuildPhase,
        setRebuildPhase,
        restoringGraph,
        setRestoringGraph,
        busy,
        aboutOpen,
        setAboutOpen,
        howToOpen,
        setHowToOpen,
        connectionError,
        setConnectionError,
        importError,
        setImportError
    }
})
