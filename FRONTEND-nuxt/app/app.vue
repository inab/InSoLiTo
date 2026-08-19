<template>
  <BApp>
    <NuxtRouteAnnouncer />
    <div v-if="showGraph">
      <GraphScreen @go-home="showGraph = false" />
    </div>
    <div v-else class="enter-webpage">
      <LandingHero @explore="showGraph = true" @about="showAbout = true" />
      <LandingFooter />
    </div>
    <LandingAboutModal v-model="showAbout" />
  </BApp>
</template>

<script setup>
const showAbout = ref(false)
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
