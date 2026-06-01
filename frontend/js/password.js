document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#password-form");
  const gaugeHost = document.querySelector("#password-gauge");
  const resultHost = document.querySelector("#password-results");

  function renderGauge(riskPercent, strength) {
    const score = Math.max(0, 100 - riskPercent);
    const radius = 82;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 100) * circumference;
    const color = window.AICipherLab.gaugeColor(score);
    gaugeHost.innerHTML = `
      <div class="radial-gauge fade-in">
        <svg viewBox="0 0 220 220" aria-hidden="true">
          <defs>
            <linearGradient id="password-ring" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="${color}"></stop>
              <stop offset="100%" stop-color="#43b7ff"></stop>
            </linearGradient>
            <filter id="ring-glow">
              <feGaussianBlur stdDeviation="4" result="coloredBlur"></feGaussianBlur>
              <feMerge>
                <feMergeNode in="coloredBlur"></feMergeNode>
                <feMergeNode in="SourceGraphic"></feMergeNode>
              </feMerge>
            </filter>
          </defs>
          <circle cx="110" cy="110" r="${radius}" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="16"></circle>
          <circle cx="110" cy="110" r="${radius}" fill="none" stroke="url(#password-ring)" stroke-width="16" stroke-linecap="round"
            filter="url(#ring-glow)"
            transform="rotate(-90 110 110)" stroke-dasharray="${circumference}" stroke-dashoffset="${circumference}">
            <animate attributeName="stroke-dashoffset" from="${circumference}" to="${offset}" dur="0.9s" fill="freeze"></animate>
          </circle>
        </svg>
        <div class="gauge-center">
          <div>
            <strong>${score}%</strong>
            <div class="label">Güvenlik skoru</div>
            <div class="badge" style="margin-top:10px;">${strength}</div>
          </div>
        </div>
      </div>
    `;
  }

  function renderResults(data) {
    renderGauge(data.risk_percent, data.strength);
    resultHost.innerHTML = `
      <div class="result-grid">
        <article class="result-card">
          <h3>Risk yüzdesi</h3>
          <strong>${data.risk_percent}%</strong>
          <p>${window.AICipherLab.warningText}</p>
        </article>
        <article class="result-card">
          <h3>AI yorumu</h3>
          <p>${data.ai_explanation}</p>
        </article>
        <article class="result-card">
          <h3>Güvenlik önerileri</h3>
          <ul class="bullet-list">${data.suggestions.map((item) => `<li>${item}</li>`).join("")}</ul>
        </article>
      </div>
      <div class="result-grid">
        <article class="result-card">
          <h3>Kontroller</h3>
          <div class="check-grid">
            ${data.checks
              .map(
                (check) => `
                  <div class="small-stat">
                    <strong class="${check.passed ? "success-text" : "danger-text"}">${check.label}</strong>
                    <p>${check.detail}</p>
                  </div>
                `
              )
              .join("")}
          </div>
        </article>
        <article class="result-card">
          <h3>Riskler</h3>
          <ul class="bullet-list">${data.issues.map((item) => `<li>${item}</li>`).join("")}</ul>
        </article>
        <article class="result-card">
          <h3>Daha güçlü alternatif örnekleri</h3>
          <ul class="bullet-list">${data.alternative_examples.map((item) => `<li>${item}</li>`).join("")}</ul>
        </article>
      </div>
    `;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const password = form.password.value;
    if (!password.trim()) {
      window.AICipherLab.toast("Analiz için parola girin.", "error");
      return;
    }
    gaugeHost.innerHTML = '<div class="centered-empty">Skor hesaplanıyor...</div>';
    resultHost.innerHTML = "";
    try {
      const data = await window.AICipherLab.api("/api/password-analyze", {
        method: "POST",
        body: JSON.stringify({ password }),
      });
      renderResults(data);
    } catch (error) {
      window.AICipherLab.toast(error.message, "error");
      gaugeHost.innerHTML = '<div class="centered-empty">Skor gösterilemiyor.</div>';
    }
  });
});
