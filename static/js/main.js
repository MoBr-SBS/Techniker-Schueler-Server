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