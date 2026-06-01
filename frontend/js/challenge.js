document.addEventListener("DOMContentLoaded", () => {
  const state = { challengeId: null };
  const cipherText = document.querySelector("#challenge-cipher-text");
  const hint = document.querySelector("#challenge-hint");
  const form = document.querySelector("#challenge-form");
  const result = document.querySelector("#challenge-result");
  const newChallenge = document.querySelector("#new-challenge");

  async function loadChallenge() {
    result.innerHTML = "";
    cipherText.textContent = "Yeni challenge oluşturuluyor...";
    try {
      const data = await window.AICipherLab.api("/api/challenge/generate", { method: "POST", body: "{}" });
      state.challengeId = data.challenge_id;
      cipherText.textContent = data.cipher_text;
      hint.textContent = data.hint;
    } catch (error) {
      window.AICipherLab.toast(error.message, "error");
      cipherText.textContent = "Challenge yüklenemedi.";
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const userGuess = form.user_guess.value.trim();
    if (!state.challengeId || !userGuess) {
      window.AICipherLab.toast("Önce challenge yüklenmeli ve tahmin girilmeli.", "error");
      return;
    }
    result.innerHTML = '<div class="centered-empty">Tahmininiz AI ile karşılaştırılıyor...</div>';
    try {
      const data = await window.AICipherLab.api("/api/challenge/evaluate", {
        method: "POST",
        body: JSON.stringify({ challenge_id: state.challengeId, user_guess: userGuess }),
      });
      result.innerHTML = `
        <div class="result-grid">
          <article class="result-card"><h3>Kullanıcının tahmini</h3><p>${data.user_guess}</p></article>
          <article class="result-card"><h3>Gerçek algoritma</h3><p>${data.actual_algorithm}</p></article>
          <article class="result-card"><h3>AI tahmini</h3><p>${data.ai_guess}</p></article>
        </div>
        <div class="result-grid">
          <article class="result-card"><h3>Gerçek çözüm</h3><div class="plaintext-output">${data.actual_plaintext}</div></article>
          <article class="result-card"><h3>AI güven oranı</h3>${window.AICipherLab.renderRing(data.ai_confidence, "AI Güveni", "small")}</article>
          <article class="result-card"><h3>Durum</h3><p>${data.user_correct ? "Tahmininiz doğru." : "Tahmininiz farklı. Bu mod eğitsel amaçlıdır."}</p><p>${data.ai_explanation}</p></article>
        </div>
      `;
    } catch (error) {
      result.innerHTML = '<div class="centered-empty">Değerlendirme alınamadı.</div>';
      window.AICipherLab.toast(error.message, "error");
    }
  });

  newChallenge.addEventListener("click", loadChallenge);
  loadChallenge();
});
