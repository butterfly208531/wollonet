/* WolloNet Search Engine — JS */

document.addEventListener('DOMContentLoaded', function () {

  // ── Dark / Light theme toggle ──────────────────────────────
  const html      = document.documentElement;
  const toggleBtn = document.getElementById('themeToggle');
  const icon      = document.getElementById('themeIcon');

  function applyTheme(theme) {
    html.setAttribute('data-theme', theme);
    localStorage.setItem('wn-theme', theme);
    if (theme === 'dark') {
      icon.className = 'bi bi-sun-fill';
      toggleBtn.title = 'Switch to light mode';
    } else {
      icon.className = 'bi bi-moon-fill';
      toggleBtn.title = 'Switch to dark mode';
    }
  }

  // Apply saved theme on load (also done inline in base.html to avoid flash)
  const savedTheme = localStorage.getItem('wn-theme') || 'light';
  applyTheme(savedTheme);

  // Toggle on click
  if (toggleBtn) {
    toggleBtn.addEventListener('click', function () {
      const current = html.getAttribute('data-theme');
      applyTheme(current === 'dark' ? 'light' : 'dark');
    });
  }

  // ── Auto-focus search input on homepage ───────────────────
  const homeInput = document.getElementById('homeQuery');
  if (homeInput) homeInput.focus();

  // ── Show/hide clear button on results page ────────────────
  const resultsInput    = document.getElementById('resultsQuery');
  const clearResultsBtn = document.getElementById('clearResultsBtn');
  if (resultsInput && clearResultsBtn) {
    function toggleClear() {
      clearResultsBtn.style.visibility = resultsInput.value ? 'visible' : 'hidden';
    }
    toggleClear();
    resultsInput.addEventListener('input', toggleClear);
  }

  // ── Keyboard shortcut: '/' focuses search ─────────────────
  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {
      e.preventDefault();
      const input = document.getElementById('resultsQuery') || document.getElementById('homeQuery');
      if (input) input.focus();
    }
  });

});
