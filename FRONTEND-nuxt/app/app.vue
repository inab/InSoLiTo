<template>
  <BApp>
    <NuxtRouteAnnouncer />
    <Transition :name="transitionName" mode="out-in">
      <div v-if="showGraph" key="graph">
        <GraphScreen :pending-restore="pendingRestore" @go-home="onGoHome" />
      </div>
      <div v-else key="landing" class="enter-webpage">
        <LandingHero @explore="onExplore" @about="uiStore.setAboutOpen(true)" />
        <LandingFooter />
      </div>
    </Transition>
    <LandingAboutModal :model-value="uiStore.aboutOpen" @update:model-value="uiStore.setAboutOpen($event)" />
  </BApp>
</template>

<script setup>
const uiStore = useUiStore()
const graphStore = useGraphStore()
const showGraph = ref(false)

// "screen-fade" everywhere except the one case it actively breaks: re-entering
// the graph screen with a graph already in the store (Explore after a previous
// search, not a fresh landing visit). That remount runs Cytoscape's synchronous
// fcose layout (see Network.vue's onMounted) on the main thread — long enough,
// often, to block Vue's own animation-frame class swap until after the layout
// (and thus the loading overlay it was supposed to cover) is already done,
// which silently eats the overlay. "screen-instant" has no matching CSS
// transition below, so Vue applies it with no animation at all — same as
// before this transition existed, only for this one case.
const transitionName = ref('screen-fade')

function onExplore () {
    transitionName.value = graphStore.nodes.length > 0 ? 'screen-instant' : 'screen-fade'
    showGraph.value = true
}

function onGoHome () {
    transitionName.value = 'screen-fade'
    showGraph.value = false
}

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

.screen-fade-enter-active,
.screen-fade-leave-active {
    transition: opacity 0.28s ease, transform 0.28s ease;
}

.screen-fade-enter-from {
    opacity: 0;
    transform: scale(1.01);
}

.screen-fade-leave-to {
    opacity: 0;
    transform: scale(0.99);
}

/* Deliberately no .screen-instant-* rules — with no matching CSS transition,
   Vue applies and removes the transition classes with no animation at all. */
</style>
