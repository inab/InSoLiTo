<template>
  <div class="landing-hero">
    <div class="landing-hero-content">
      <img src="~/assets/images/logo_InSoLiTo.png" alt="InSoLiTo Logo" class="landing-hero-logo">
      <p class="landing-tagline">Interactions of Software for Life Sciences Tools</p>
      <p class="landing-description">
        Explore the co-usage network of bioinformatics research software.
        Discover how tools relate through shared citations in scientific publications.
      </p>
      <div class="landing-hero-actions">
        <BButton class="landing-cta" @click="$emit('explore')">
          Explore the graph &rarr;
        </BButton>
        <BButton variant="outline-primary" class="landing-about-btn" @click="$emit('about')">
          About
        </BButton>
      </div>
    </div>

    <div class="landing-hero-illustration" aria-hidden="true">
      <svg viewBox="0 0 400 400" class="graph-svg">
        <g class="graph-edges">
          <line x1="200" y1="200" x2="80" y2="140" />
          <line x1="200" y1="200" x2="180" y2="90" />
          <line x1="200" y1="200" x2="260" y2="160" />
          <line x1="200" y1="200" x2="120" y2="260" />
          <line x1="200" y1="200" x2="220" y2="300" />
          <line x1="200" y1="200" x2="320" y2="270" />
          <line x1="260" y1="160" x2="340" y2="110" />
          <line x1="220" y1="300" x2="320" y2="270" />
          <line x1="320" y1="270" x2="370" y2="340" />
          <line x1="80" y1="140" x2="120" y2="260" />
        </g>
        <g class="graph-nodes">
          <circle cx="200" cy="200" r="16" class="node node-hub" style="animation-delay:0s" />
          <circle cx="80" cy="140" r="12" class="node node-primary" style="animation-delay:0.3s" />
          <circle cx="180" cy="90" r="9" class="node node-primary" style="animation-delay:0.6s" />
          <circle cx="260" cy="160" r="17" class="node node-secondary" style="animation-delay:0.9s" />
          <circle cx="340" cy="110" r="8" class="node node-primary" style="animation-delay:1.2s" />
          <circle cx="120" cy="260" r="10" class="node node-primary" style="animation-delay:1.5s" />
          <circle cx="220" cy="300" r="13" class="node node-secondary" style="animation-delay:1.8s" />
          <circle cx="320" cy="270" r="10" class="node node-primary" style="animation-delay:2.1s" />
          <circle cx="370" cy="340" r="8" class="node node-primary" style="animation-delay:2.4s" />
        </g>
      </svg>
    </div>
  </div>
</template>

<script setup>
defineEmits(['explore', 'about'])
</script>

<style scoped>
.landing-hero {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4rem;
    padding: 40px 60px;
}

.landing-hero-content {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    text-align: left;
    max-width: 460px;
}

.landing-hero-logo {
    height: 120px;
    margin-bottom: 12px;
}

.landing-tagline {
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 3px;
    color: var(--insolito-primary);
    text-transform: uppercase;
    margin: 0;
}

.landing-description {
    font-size: 1.05rem;
    color: var(--insolito-text-muted);
    line-height: 1.6;
    margin: 16px 0 28px;
}

.landing-hero-actions {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}

.landing-cta {
    background: var(--insolito-secondary);
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 14px 36px;
    font-size: 1rem;
    font-weight: 600;
    transition: background 0.2s, transform 0.2s;
}

.landing-cta:hover {
    background: var(--insolito-secondary-hover);
    color: #fff;
    transform: translateY(-2px);
}

.landing-about-btn {
    border-radius: 6px;
    padding: 14px 28px;
    font-size: 1rem;
    font-weight: 600;
    color: var(--insolito-primary);
    border-color: var(--insolito-primary);
}

.landing-about-btn:hover {
    background: var(--insolito-primary);
    border-color: var(--insolito-primary);
    color: #fff;
}

.landing-hero-illustration {
    flex: 1;
    max-width: 440px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.graph-svg {
    width: 100%;
    height: auto;
}

.graph-edges line {
    stroke: var(--insolito-edge);
    stroke-width: 1.5;
}

.node {
    transform-origin: center;
    transform-box: fill-box;
    animation: node-pulse 4s ease-in-out infinite;
}

.node-primary {
    fill: var(--insolito-node-primary);
}

.node-secondary {
    fill: var(--insolito-node-secondary);
}

.node-hub {
    fill: var(--insolito-primary-dark);
}

@keyframes node-pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.18); }
}

@media (max-width: 900px) {
    .landing-hero {
        flex-direction: column;
        text-align: center;
        gap: 2rem;
        padding: 32px 24px;
    }

    .landing-hero-content {
        align-items: center;
        text-align: center;
    }

    .landing-hero-actions {
        justify-content: center;
    }

    .landing-hero-illustration {
        max-width: 280px;
    }
}

@media (max-width: 480px) {
    .landing-hero-logo {
        height: 88px;
    }

    .landing-hero-actions {
        flex-direction: column;
        align-items: stretch;
        width: 100%;
    }

    .landing-cta,
    .landing-about-btn {
        width: 100%;
        text-align: center;
    }
}
</style>
