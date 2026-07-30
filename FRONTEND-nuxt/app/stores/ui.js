export const useUiStore = defineStore('ui', () => {
    const sidebarOpen = ref(false)
    const legendOpen = ref(false)

    function toggleSidebar () {
        sidebarOpen.value = !sidebarOpen.value
    }

    function setSidebarOpen (open) {
        sidebarOpen.value = open
    }

    function toggleLegend () {
        legendOpen.value = !legendOpen.value
    }

    return { sidebarOpen, toggleSidebar, setSidebarOpen, legendOpen, toggleLegend }
})
