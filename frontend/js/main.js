(function () {
  const toastStack = document.createElement("div");
  toastStack.className = "toast-stack";
  document.addEventListener("DOMContentLoaded", () => {
    document.body.appendChild(toastStack);
    setupNav();
    markActiveNav();
    syncYear();
  });

  function setupNav() {
    const toggle = document.querySelector("[data-nav-toggle]");
    const menu = document.querySelector("[data-nav-menu]");
    if (!toggle || !menu) {
      return;
    }
    toggle.addEventListener("click", () => {
      const next = !menu.classList.contains("open");
      menu.classList.toggle("open", next);
      toggle.setAttribute("aria-expanded", String(next));
    });
    menu.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        menu.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  function markActiveNav() {
    const page = location.pathname.split("/").pop() || "index.html";
    document.querySelectorAll(".nav-link").forEach((link) => {
      const href = link.getAttribute("href");
      if (href === page || (page === "" && href === "index.html")) {
        link.classList.add("active");
      }
    });
  }

  function syncYear() {
    document.querySelectorAll("[data-year]").forEach((node) => {
      node.textContent = String(new Date().getFullYear());
    });
  }

  function createRingMarkup(score, label, size) {
    const radius = 72;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 100) * circumference;
    const color = score >= 70 ? "#46e2a0" : score >= 45 ? "#ffd166" : "#ff6b8a";
    return `
      <div class="${size === "small" ? "mini-ring" : "confidence-ring"}" style="width:${size === "small" ? 160 : 220}px;">
        <svg viewBox="0 0 180 180" aria-hidden="true">
          <defs>
            <linearGradient id="ring-gradient-${size}-${score}" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="${color}" />
              <stop offset="100%" stop-color="#43b7ff" />
            </linearGradient>
          </defs>
          <circle cx="90" cy="90" r="${radius}" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="12"></circle>
          <circle cx="90" cy="90" r="${radius}" fill="none" stroke="url(#ring-gradient-${size}-${score})" stroke-width="12" stroke-linecap="round"
            transform="rotate(-90 90 90)" stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"></circle>
        </svg>
        <div class="ring-center">
          <div>
            <strong>${score}%</strong>
            <span>${label}</span>
          </div>
        </div>
      </div>
    `;
  }

  window.AICipherLab = {
    api(path, options = {}) {
      return fetch(path, {
        headers: {
          "Content-Type": "application/json",
          ...(options.headers || {}),
        },
        ...options,
      }).then(async (response) => {
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          const message = data.detail || "Beklenmeyen bir hata oluştu.";
          throw new Error(message);
        }
        return data;
      });
    },
    toast(message, type = "info") {
      const toast = document.createElement("div");
      toast.className = `toast ${type === "error" ? "error" : ""}`;
      toast.textContent = message;
      toastStack.appendChild(toast);
      window.setTimeout(() => toast.remove(), 3200);
    },
    warningText:
      "Bu sistem eğitim amaçlıdır. AES ve RSA gibi modern şifreleme algoritmaları anahtar olmadan çözülemez. Buradaki analiz sistemi klasik şifreleme yöntemleri üzerinde çalışmaktadır.",
    copy(text) {
      navigator.clipboard.writeText(text).then(
        () => window.AICipherLab.toast("Sonuç panoya kopyalandı."),
        () => window.AICipherLab.toast("Kopyalama başarısız oldu.", "error")
      );
    },
    renderRing(score, label, size = "large") {
      return createRingMarkup(score, label, size);
    },
    gaugeColor(score) {
      if (score >= 70) return "#46e2a0";
      if (score >= 45) return "#ffd166";
      return "#ff6b8a";
    },
  };
})();
