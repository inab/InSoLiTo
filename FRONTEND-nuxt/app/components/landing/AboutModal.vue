<template>
  <BModal
    :model-value="modelValue"
    title="About InSoLiTo"
    size="lg"
    ok-only
    ok-title="Close"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <section class="about-section">
      <h6>What is InSoLiTo?</h6>
      <p>
        <strong>InSoLiTo</strong> (Interactions of Software for Life Sciences Tools) is a graph-based
        web application that visualises the co-usage network of bioinformatics research software from
        the <a href="https://openebench.bsc.es" target="_blank" rel="noopener noreferrer">OpenEBench</a>
        collection.
      </p>
    </section>

    <hr>
    <section class="about-section">
      <h6>How the graph is built</h6>
      <p>
        An edge between two tools does not mean one cites the other, or that they are used together in
        a pipeline — it means both were cited together in the reference list of the same publication
        (co-citation), derived from <a href="https://pubmed.ncbi.nlm.nih.gov" target="_blank" rel="noopener noreferrer">PubMed</a>
        data cross-referenced with OpenEBench.
      </p>
      <p class="mb-0">
        Topics are labelled using the <a href="https://edamontology.org" target="_blank" rel="noopener noreferrer">EDAM</a>
        ontology, and thematic communities are detected purely from co-citation density (Louvain clustering) —
        the two are independent, so a community's dominant topic is only an approximation of what it contains.
      </p>
    </section>

    <hr>
    <section class="about-section">
      <h6>Credits</h6>
      <p>
        Originally developed by Sergi Aguiló Castillo at the
        <a href="https://www.bsc.es" target="_blank" rel="noopener noreferrer">Barcelona Supercomputing Center</a>,
        within the <a href="https://elixir-europe.org" target="_blank" rel="noopener noreferrer">ELIXIR</a> /
        <a href="https://inb-elixir.es/" target="_blank" rel="noopener noreferrer">INB</a> ecosystem. See the full
        <a href="https://upcommons.upc.edu/entities/publication/77d4990b-48f2-4463-9fe6-09cddef064c9" target="_blank" rel="noopener noreferrer">thesis</a>
        and related
        <a href="https://f1000research.com/search?q=insolito" target="_blank" rel="noopener noreferrer">posters</a>
        for further detail.
      </p>
    </section>

    <hr>
    <section class="about-section">
      <h6>Cite this work</h6>
      <p class="mb-0">
        Aguiló-Castillo, S. (2022). <em>InSoLiTo dataset</em> (Version v8) [Data set]. Zenodo.<br>
        <a href="https://doi.org/10.5281/zenodo.7524268" target="_blank" rel="noopener noreferrer">doi:10.5281/zenodo.7524268</a>
      </p>
    </section>

    <hr>
    <section class="about-section">
      <h6>Contribute</h6>
      <p class="mb-0">
        InSoLiTo is open source — bug reports, feature ideas and pull requests are welcome on
        <a href="https://github.com/inab/InSoLiTo" target="_blank" rel="noopener noreferrer">
          <img src="~/assets/images/github.svg" alt="GitHub" class="github-icon">GitHub
        </a>.
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
.about-section h6 {
    text-transform: uppercase;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: var(--insolito-text-muted);
    margin-bottom: 0.5rem;
}

.github-icon {
    height: 18px;
    margin-right: 4px;
    vertical-align: middle;
}
</style>
