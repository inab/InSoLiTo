// Animates a ref from 0 to `target` over `duration`ms (easeOutCubic — fast start,
// gentle settle, reads better for a landing-page stat than linear or bouncy easing).
// `target` is captured once at creation time: every current caller (DatasetStats.vue)
// already knows its number synchronously from the bundled JSON, so there's no need
// to support retargeting an in-flight animation.
//
// Callers must destructure { value, start } and use `value` directly in the
// template (not `someObj.value` where someObj is the whole returned object) —
// Vue only auto-unwraps a ref that's a top-level <script setup> binding; a ref
// nested one level down in a plain object stays a Ref instance in the template,
// and calling .toLocaleString() on that silently falls through to
// Object.prototype's version and renders "[object Object]" instead of erroring.
export function useCountUp (target, duration = 3000) {
    const value = ref(0)
    let frame = null

    function start () {
        const startTime = performance.now()
        function tick (now) {
            const progress = Math.min((now - startTime) / duration, 1)
            const eased = 1 - Math.pow(1 - progress, 3)
            value.value = Math.round(target * eased)
            if (progress < 1) frame = requestAnimationFrame(tick)
        }
        frame = requestAnimationFrame(tick)
    }

    onUnmounted(() => { if (frame) cancelAnimationFrame(frame) })

    return { value, start }
}
