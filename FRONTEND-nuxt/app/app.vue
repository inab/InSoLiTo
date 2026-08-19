<template>
  <BApp>
    <NuxtRouteAnnouncer />
    <div v-if="showGraph">
      <GraphScreen @go-home="showGraph = false" />
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
