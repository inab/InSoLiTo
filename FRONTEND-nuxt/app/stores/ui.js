export const useUiStore = defineStore('ui', () => {
    const sidebarOpen = ref(false)

    function toggleSidebar () {
        sidebarOpen.value = !sidebarOpen.value
    }

    function setSidebarOpen (open) {
        sidebarOpen.value = open
    }

    return { sidebarOpen, toggleSidebar, setSidebarOpen }
})
