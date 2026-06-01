document.addEventListener("DOMContentLoaded", () => {
  const algorithm = document.querySelector("#algorithm");
  const extraShift = document.querySelector("[data-shift-field]");
  const extraKey = document.querySelector("[data-key-field]");
  const form = document.querySelector("#encrypt-form");
  const result = document.querySelector("#encrypt-result");
  const copyButton = document.querySelector("#copy-result");
  const clearButton = document.querySelector("#clear-form");

  function syncFields() {
    extraShift.classList.toggle("hidden", algorithm.value !== "caesar");
    extraKey.classList.toggle("hidden", algorithm.value !== "vigenere");
  }

  algorithm.addEventListener("change", syncFields);
  syncFields();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      text: form.text.value.trim(),
      algorithm: algorithm.value,
      shift: form.shift.value ? Number(form.shift.value) : undefined,
      key: form.key.value.trim() || undefined,
    };
    if (!payload.text) {
      window.AICipherLab.toast("Lütfen şifrelenecek metni girin.", "error");
      return;
    }
    try {
      result.textContent = "Şifreleme çalışıyor...";
      const data = await window.AICipherLab.api("/api/encrypt", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      result.textContent = data.result;
    } catch (error) {
      result.textContent = "Sonuç alınamadı.";
      window.AICipherLab.toast(error.message, "error");
    }
  });

  copyButton.addEventListener("click", () => window.AICipherLab.copy(result.textContent));
  clearButton.addEventListener("click", () => {
    form.reset();
    syncFields();
    result.textContent = "Sonuç burada görünecek.";
  });
});
