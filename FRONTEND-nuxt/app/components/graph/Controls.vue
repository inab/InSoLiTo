<template>
  <div>
    <div class="graph-controls" :class="{ 'graph-controls-with-sidebar': uiStore.sidebarOpen }">
      <div class="graph-controls-pad">
        <button type="button" class="graph-controls-btn graph-controls-btn-up" aria-label="Pan up" @click="$emit('pan', 0, -1)">
          <svg viewBox="0 0 24 24" class="graph-controls-icon"><path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
        </button>
        <button type="button" class="graph-controls-btn graph-controls-btn-left" aria-label="Pan left" @click="$emit('pan', -1, 0)">
          <svg viewBox="0 0 24 24" class="graph-controls-icon"><path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
        </button>
        <button type="button" class="graph-controls-btn graph-controls-btn-fit" aria-label="Fit graph to screen" @click="$emit('fit')">
          <svg viewBox="0 0 24 24" class="graph-controls-icon">
            <path d="M9 3H4v5M15 3h5v5M9 21H4v-5M15 21h5v-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
        <button type="button" class="graph-controls-btn graph-controls-btn-right" aria-label="Pan right" @click="$emit('pan', 1, 0)">
          <svg viewBox="0 0 24 24" class="graph-controls-icon"><path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
        </button>
        <button type="button" class="graph-controls-btn graph-controls-btn-down" aria-label="Pan down" @click="$emit('pan', 0, 1)">
          <svg viewBox="0 0 24 24" class="graph-controls-icon"><path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
        </button>
      </div>
      <div class="graph-controls-zoom">
        <button type="button" class="graph-controls-btn" aria-label="Zoom in" @click="$emit('zoom-in')">+</button>
        <button type="button" class="graph-controls-btn" aria-label="Zoom out" @click="$emit('zoom-out')">&minus;</button>
      </div>
    </div>

    <!-- Mobile only (see media query below): pan/zoom buttons are redundant with
         drag/pinch touch gestures there, and the full widget collides with
         SelectionInfoPanel's full-width bottom bar. Fit/reset has no touch-gesture
         equivalent though (no easy way to "undo" a wild drag/pinch), so it's kept
         as a single small button instead of dropped entirely. -->
    <button type="button" class="graph-controls-mobile-fit" aria-label="Fit graph to screen" @click="$emit('fit')">
      <svg viewBox="0 0 24 24" class="graph-controls-icon">
        <path d="M9 3H4v5M15 3h5v5M9 21H4v-5M15 21h5v-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </button>
  </div>
</template>

<script setup>
const uiStore = useUiStore()

defineEmits(['pan', 'fit', 'zoom-in', 'zoom-out'])
</script>

<style scoped>
.graph-controls {
    position: fixed;
    bottom: 20px;
    left: 20px;
    z-index: 18;
    display: flex;
    align-items: flex-end;
    gap: 8px;
    transition: left 0.3s ease;
}

/* --graph-sidebar-width is defined on .graph-screen (Screen.vue) — inherited here
   like any CSS custom property, `scoped` only affects selector writing, not reads. */
.graph-controls-with-sidebar {
    left: calc(var(--graph-sidebar-width) + 16px);
}

.graph-controls-pad {
    display: grid;
    grid-template-columns: repeat(3, 32px);
    grid-template-rows: repeat(3, 32px);
    gap: 2px;
    background: var(--insolito-bg);
    border-radius: 8px;
    box-shadow: 0 6px 24px rgba(28, 43, 58, 0.24);
    padding: 4px;
}

.graph-controls-btn-up { grid-column: 2; grid-row: 1; }
.graph-controls-btn-left { grid-column: 1; grid-row: 2; }
.graph-controls-btn-fit { grid-column: 2; grid-row: 2; }
.graph-controls-btn-right { grid-column: 3; grid-row: 2; }
.graph-controls-btn-down { grid-column: 2; grid-row: 3; }

.graph-controls-btn-up .graph-controls-icon { transform: rotate(-90deg); }
.graph-controls-btn-down .graph-controls-icon { transform: rotate(90deg); }
.graph-controls-btn-left .graph-controls-icon { transform: rotate(180deg); }

.graph-controls-zoom {
    display: flex;
    flex-direction: column;
    gap: 2px;
    background: var(--insolito-bg);
    border-radius: 8px;
    box-shadow: 0 6px 24px rgba(28, 43, 58, 0.24);
    padding: 4px;
}

.graph-controls-btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: none;
    border: none;
    border-radius: 4px;
    color: var(--insolito-text);
    font-size: 1.1rem;
    line-height: 1;
    cursor: pointer;
}

.graph-controls-btn:hover {
    background: var(--insolito-bg-footer);
    color: var(--insolito-primary);
}

.graph-controls-icon {
    width: 18px;
    height: 18px;
}

.graph-controls-mobile-fit {
    display: none;
}

@media (max-width: 600px) {
    .graph-controls {
        display: none;
    }

    /* Same row/size as .sidebar-toggle (top:20, 40px circle) — Legend starts lower
       (top:76px) on mobile specifically to clear that row, so the right side of it
       is free. */
    .graph-controls-mobile-fit {
        display: flex;
        position: fixed;
        top: 20px;
        right: 16px;
        z-index: 18;
        width: 40px;
        height: 40px;
        align-items: center;
        justify-content: center;
        background: var(--insolito-bg);
        border: 1px solid var(--insolito-border);
        border-radius: 50%;
        color: var(--insolito-primary);
        cursor: pointer;
        box-shadow: 0 2px 6px rgba(28, 43, 58, 0.12);
    }
}
</style>
