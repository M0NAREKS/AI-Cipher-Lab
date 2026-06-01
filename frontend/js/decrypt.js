document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#decrypt-form");
  const processList = document.querySelector("#process-list");
  const resultPanel = document.querySelector("#decrypt-results");
  const steps = [
    "Caesar test ediliyor...",
    "Atbash taranıyor...",
    "Base64 analiz ediliyor...",
    "Hex format kontrolü yapılıyor...",
    "Vigenere adayları değerlendiriliyor...",
    "AI kararı hazırlanıyor...",
  ];
  let timerId;

  function renderSteps(activeIndex = -1, doneCount = -1) {
    processList.innerHTML = steps
      .map((step, index) => {
        const state = index < doneCount ? "done" : index === activeIndex ? "active" : "";
        return `<div class="process-step ${state}"><span class="dot"></span><span>${step}</span></div>`;
      })
      .join("");
  }

  function startLiveProcess() {
    renderSteps(0, -1);
    let index = 0;
    timerId = window.setInterval(() => {
      index = (index + 1) % steps.length;
      renderSteps(index, index - 1);
    }, 850);
  }

  function stopLiveProcess() {
    window.clearInterval(timerId);
    renderSteps(-1, steps.length);
  }

  function renderAttempts(attempts) {
    return attempts
      .map(
        (attempt) => `
          <article class="attempt-card">
            <strong>${attempt.algorithm}</strong>
            <small>${attempt.parameter || "parametre yok"}</small>
            <div class="score">Final skor: ${attempt.final_score} | Heuristic: ${attempt.heuristic_score}</div>
            <small>${attempt.reason}</small>
            <small>Sözlük: ${attempt.dictionary_match_count} | Doğallık: ${attempt.naturalness_score} | Ceza: ${attempt.gibberish_penalty}</small>
            <div class="code-output">${attempt.decoded_text}</div>
          </article>
        `
      )
      .join("");
  }

  function renderResult(data) {
    const primary =
      data.final_best_match ||
      data.llm_selected_match ||
      data.heuristic_best_match ||
      data.attempts?.[0];
    if (!primary) {
      resultPanel.innerHTML = '<div class="centered-empty">Geçerli sonuç bulunamadı.</div>';
      return;
    }

    resultPanel.innerHTML = `
      <article class="result-card fade-in">
        <div class="result-main">
          <div>${window.AICipherLab.renderRing(primary.confidence || 0, "Güven")}</div>
          <div class="stack">
            <div>
              <div class="badge">${data.used_llm ? "LLM Seçimi" : "Heuristic Seçimi"}</div>
              <h3>Çözülmüş Metin</h3>
              <div class="plaintext-output">${primary.decoded_text}</div>
            </div>
            <div class="result-grid">
              <article class="result-card">
                <h3>Yöntem</h3>
                <p>${primary.algorithm}</p>
              </article>
              <article class="result-card">
                <h3>Parametre</h3>
                <p>${primary.parameter || "yok"}</p>
              </article>
              <article class="result-card">
                <h3>Güven</h3>
                <p>%${primary.confidence || 0}</p>
              </article>
            </div>
          </div>
        </div>
      </article>
      <div class="result-grid">
        <article class="result-card">
          <h3>AI Yorumu</h3>
          <p>${primary.reason || data.ai_commentary}</p>
        </article>
        <article class="result-card">
          <h3>Teknik Açıklama</h3>
          <p>${data.technical_explanation}</p>
        </article>
        <article class="result-card">
          <h3>Modern Sistemlerde Durumu</h3>
          <p>${data.modern_relevance}</p>
        </article>
      </div>
      <div class="result-grid">
        <article class="result-card">
          <h3>Güçlü Yönler</h3>
          <ul class="bullet-list">${data.strengths.map((item) => `<li>${item}</li>`).join("")}</ul>
        </article>
        <article class="result-card">
          <h3>Zayıf Yönler</h3>
          <ul class="bullet-list">${data.weaknesses.map((item) => `<li>${item}</li>`).join("")}</ul>
        </article>
        <article class="result-card">
          <h3>AI Durumu</h3>
          <p>${data.ai_available ? "Groq aday seçimi veya yorum katmanı aktif." : "AI kullanılamadı; heuristic final seçim kullanıldı."}</p>
        </article>
      </div>
      <section class="section">
        <div class="section-header">
          <h3>Tüm Denemeler</h3>
        </div>
        <div class="attempt-grid">
          ${renderAttempts(data.attempts)}
        </div>
      </section>
    `;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const cipherText = form.cipher_text.value.trim();
    if (!cipherText) {
      window.AICipherLab.toast("Analiz için şifreli metin girin.", "error");
      return;
    }
    resultPanel.innerHTML = "";
    startLiveProcess();
    try {
      const data = await window.AICipherLab.api("/api/decrypt-detect", {
        method: "POST",
        body: JSON.stringify({ cipher_text: cipherText }),
      });
      stopLiveProcess();
      renderResult(data);
    } catch (error) {
      stopLiveProcess();
      resultPanel.innerHTML = '<div class="centered-empty">Analiz tamamlanamadı.</div>';
      window.AICipherLab.toast(error.message, "error");
    }
  });

  renderSteps();
});
