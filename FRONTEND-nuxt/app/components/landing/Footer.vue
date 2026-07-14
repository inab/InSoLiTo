<template>
  <div class="landing-footer">
    <a href="https://www.bsc.es" target="_blank" rel="noopener noreferrer">
      <img src="~/assets/images/BSC-blue.svg" alt="BSC" class="footer-logo">
    </a>
    <a href="https://inb-elixir.es/" target="_blank" rel="noopener noreferrer">
      <img src="~/assets/images/logoINB-ELIXIR_ES.png" alt="INB / ELIXIR" class="footer-logo">
    </a>
    <a href="https://openebench.bsc.es/" target="_blank" rel="noopener noreferrer">
      <img src="~/assets/images/openebench.gif" alt="OpenEBench" class="footer-logo">
    </a>
    <a href="https://github.com/inab/InSoLiTo" target="_blank" rel="noopener noreferrer">
      <img src="~/assets/images/github.svg" alt="GitHub" class="footer-logo footer-logo-github">
    </a>
  </div>
</template>

<style scoped>
.landing-footer {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: center;
    gap: 40px;
    padding: 20px 40px;
    background: var(--insolito-bg-footer);
    border-top: 1px solid var(--insolito-border);
    flex-shrink: 0;
}

.footer-logo {
    height: 44px;
    object-fit: contain;
    opacity: 0.85;
    transition: opacity 0.2s;
}

.footer-logo:hover {
    opacity: 1;
}

.footer-logo-github {
    height: 36px;
    filter: brightness(0);
}

@media (max-width: 480px) {
    .landing-footer {
        gap: 26px;
        padding: 16px 20px;
    }

    .footer-logo {
        height: 34px;
    }

    .footer-logo-github {
        height: 28px;
    }
}
</style>
