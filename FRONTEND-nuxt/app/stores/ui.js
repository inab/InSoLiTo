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
        resetLayers
    }
})
