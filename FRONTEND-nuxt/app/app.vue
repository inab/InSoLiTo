<template>
  <BApp>
    <NuxtRouteAnnouncer />
    <div class="enter-webpage">
      <LandingHero @explore="onExplore" @about="showAbout = true" />
      <LandingFooter />
    </div>
    <LandingAboutModal v-model="showAbout" />
  </BApp>
</template>

<script setup>
const showAbout = ref(false)

function onExplore () {
    // Placeholder until the graph view exists (plan step 5+)
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
