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
        <strong>Topic</strong> is broader: it walks the <a href="https://edamontology.org" target="_blank" rel="noopener noreferrer">EDAM</a> ontology's subclass hierarchy and pulls in
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
      <p class="mb-0">
        A <strong>solid</strong> edge is a direct co-citation. A <strong>dashed</strong> edge means the
        Publication in the middle is connected to two or more different Tools/Databases in the current
        graph (a Tool&ndash;Publication&ndash;Tool bridge) — the two dashed edges don't necessarily come
        from the same underlying citation, so it's a weaker, more ambiguous signal than a direct edge
        between two tools.
      </p>
      <img src="~/assets/images/how-to-use-edge-styles.png" alt="Solid edges for direct co-citations, dashed edges for a Publication bridging two Tools" class="how-to-screenshot">
    </section>

    <hr>
    <section class="how-to-section">
      <h6>Clicking nodes and edges</h6>
      <p>
        Click any node or edge to open an info panel next to it. A <strong>Tool</strong> or
        <strong>Database</strong> node shows its name, topic, a link to its OpenEBench webpage, and a
        button to add it to your active search if it isn't already there.
      </p>
      <img src="~/assets/images/how-to-use-node-tool.png" alt="Info panel for a clicked Tool node" class="how-to-screenshot">
      <p>
        A <strong>Publication</strong> node shows its title, year, topic, and DOI/PubMed links when
        available.
      </p>
      <img src="~/assets/images/how-to-use-node-publication.png" alt="Info panel for a clicked Publication node" class="how-to-screenshot">
      <p class="mb-0">
        An <strong>edge</strong> shows the two nodes it connects, the total number of co-citations, and a
        year-by-year breakdown.
      </p>
      <img src="~/assets/images/how-to-use-edge-cocitation.png" alt="Info panel for a clicked edge, with a year-by-year co-citation breakdown" class="how-to-screenshot">
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
      <h6>Legend</h6>
      <p class="mb-0">
        Click a legend entry to hide every node of that type (or community) and its edges — click it
        again to bring them back. The node you searched for is exempt and always stays visible, even if
        you hide its own type or community.
      </p>
      <img src="~/assets/images/how-to-use-legend-toggle.png" alt="Legend with the Publication toggle switched off" class="how-to-screenshot">
    </section>

    <hr>
    <section class="how-to-section">
      <h6>The highlighted node</h6>
      <p>
        The <strong>diamond-shaped</strong> node, with a thicker border and a larger, bold label, is the
        exact term you searched for — it always stays visible and colored normally, even if you hide its
        type or cluster in the legend.
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

.how-to-screenshot {
    display: block;
    max-width: 100%;
    max-height: 260px;
    width: auto;
    border: 1px solid var(--insolito-border);
    border-radius: 8px;
    margin: 12px 0;
}
</style>
