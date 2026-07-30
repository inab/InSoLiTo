export const useUiStore = defineStore('ui', () => {
    const sidebarOpen = ref(false)
    const legendOpen = ref(false)
    // 'type' colors nodes by Tool/Database/Publication; 'topic' colors them by
    // their Louvain community (shared with Network.vue and Legend.vue).
    const colorMode = ref('type')

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

    return { sidebarOpen, toggleSidebar, setSidebarOpen, legendOpen, toggleLegend, colorMode, setColorMode }
})
