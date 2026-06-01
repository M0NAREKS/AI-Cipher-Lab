document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#battle-form");
  const grid = document.querySelector("#battle-results");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      text: form.text.value.trim(),
      shift: Number(form.shift.value || 3),
      key: form.key.value.trim() || "CRYPTO",
    };
    if (!payload.text) {
      window.AICipherLab.toast("Karşılaştırma için bir metin girin.", "error");
      return;
    }
    grid.innerHTML = '<div class="centered-empty">Algoritmalar aynı anda çalıştırılıyor...</div>';
    try {
      const data = await window.AICipherLab.api("/api/cipher-battle", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      grid.innerHTML = data.results
        .map(
          (item) => `
            <article class="battle-card fade-in">
              <div class="badge">${item.algorithm}</div>
              <p>${JSON.stringify(item.meta)}</p>
              <div class="code-output">${item.output}</div>
              <div class="result-actions">
                <button class="ghost-button" data-copy="${encodeURIComponent(item.output)}">Kopyala</button>
              </div>
            </article>
          `
        )
        .join("");
      grid.querySelectorAll("[data-copy]").forEach((button) => {
        button.addEventListener("click", () => window.AICipherLab.copy(decodeURIComponent(button.dataset.copy)));
      });
    } catch (error) {
      grid.innerHTML = '<div class="centered-empty">Sonuçlar yüklenemedi.</div>';
      window.AICipherLab.toast(error.message, "error");
    }
  });
});
