(function () {
  const el = document.getElementById("clock");
  if (!el) return;
  function tick() {
    const now = new Date();
    el.textContent = now.toLocaleTimeString("de-DE");
  }
  tick();
  setInterval(tick, 1000);
})();

(function () {
  const btn  = document.getElementById("theme-toggle");
  const icon = document.getElementById("theme-icon");
  if (!btn) return;

  function isLight() {
    return document.documentElement.getAttribute("data-theme") === "light";
  }

  function applyIcon() {
    icon.setAttribute("data-lucide", isLight() ? "moon" : "sun");
    lucide.createIcons();
  }

  applyIcon();

  btn.addEventListener("click", function () {
    if (isLight()) {
      document.documentElement.removeAttribute("data-theme");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.setAttribute("data-theme", "light");
      localStorage.setItem("theme", "light");
    }
    applyIcon();
  });
})();