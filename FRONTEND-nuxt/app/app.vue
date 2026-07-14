<template>
  <BApp>
    <NuxtRouteAnnouncer />
    <div v-if="showGraph">
      <GraphScreen @reset="onReset" />
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

function onReset () {
    // Placeholder until graph store/wrapper exists (plan step 4/5)
}
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
