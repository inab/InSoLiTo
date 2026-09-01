<template>
  <BApp>
    <NuxtRouteAnnouncer />
    <div v-if="showGraph">
      <GraphScreen :pending-restore="pendingRestore" @go-home="showGraph = false" />
    </div>
    <div v-else class="enter-webpage">
      <LandingHero @explore="showGraph = true" @about="uiStore.setAboutOpen(true)" />
      <LandingFooter />
    </div>
    <LandingAboutModal :model-value="uiStore.aboutOpen" @update:model-value="uiStore.setAboutOpen($event)" />
  </BApp>
</template>

<script setup>
const uiStore = useUiStore()
const showGraph = ref(false)

// A "Share" link (?state=...) — decoded once, before the landing page ever
// shows, so a shared link opens straight into the reconstructed graph instead of
// requiring an extra click through the landing page first.
const pendingRestore = ref(null)
onMounted(() => {
    const state = parseShareState()
    if (state) {
        pendingRestore.value = state
        showGraph.value = true
    }
})
</script>

<style scoped>
.enter-webpage {
    width: 100%;
    min-height: 100vh;
    background: var(--insolito-bg);
    display: flex;
    flex-direction: column;
}
</style>
