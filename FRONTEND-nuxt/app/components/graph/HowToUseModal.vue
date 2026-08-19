<template>
  <BModal
    :model-value="modelValue"
    title="How to use InSoLiTo"
    size="lg"
    ok-only
    ok-title="Close"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <section class="how-to-section">
      <h6>What you searched for</h6>
      <p>
        Searching a <strong>Tool</strong> or <strong>Database</strong> matches it exactly. Searching a
        <strong>Topic</strong> is broader: it walks the EDAM ontology's subclass hierarchy and pulls in
        every tool tagged with that topic <em>or</em> any of its more specific sub-topics, then draws
        every co-citation edge among all of them at once.
      </p>
    </section>

    <hr>
    <section class="how-to-section">
      <h6>What an edge means</h6>
      <p>
        An edge is a <strong>co-citation</strong>, not a citation and not shared usage in a pipeline: it
        means some third publication cited both endpoints together in its own reference list. It does not
        mean one endpoint cites the other, or that they were ever used together in practice. The thicker
        the edge, the more publications co-cite that pair.
      </p>
    </section>

    <hr>
    <section class="how-to-section">
      <h6>Node colors</h6>
      <p>
        In <strong>By type</strong> mode, color reflects what a node is: Tool, Database, or Publication.
        In <strong>By topic</strong> mode, color reflects the node's community — a cluster detected purely
        from how densely tools co-cite each other, with no input from EDAM. The topic label shown in the
        legend is just the most common EDAM topic within that cluster, so a community can still mix
        several topics.
      </p>
    </section>

    <hr>
    <section class="how-to-section">
      <h6>The highlighted node</h6>
      <p>
        The node with the thicker border and bold label is the exact term you searched for — it always
        stays visible and colored normally, even if you hide its type or cluster in the legend.
      </p>
    </section>

    <hr>
    <section class="how-to-section">
      <h6>Filters</h6>
      <p class="mb-0">
        The publication year range and minimum co-citations sliders apply to every active search at once,
        but only when you press <strong>Search</strong> — dragging a slider doesn't update the graph on
        its own.
      </p>
    </section>
  </BModal>
</template>

<script setup>
defineProps({
    modelValue: {
        type: Boolean,
        default: false
    }
})
defineEmits(['update:modelValue'])
</script>

<style scoped>
.how-to-section h6 {
    text-transform: uppercase;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: var(--insolito-text-muted);
    margin-bottom: 0.5rem;
}
</style>
