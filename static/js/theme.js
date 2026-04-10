/**
 * theme.js — Arctic Nord Light / Dark Theme Toggle
 * =================================================
 * Responsibilities:
 *   1. Read the user's saved preference from localStorage on every page load
 *      (the <html> data-theme attr is already set by the inline script in
 *      base.html before the stylesheet loads, so there is zero flash)
 *   2. Wire the toggle button to flip between "dark" and "light"
 *   3. Persist the choice to localStorage so it survives page navigation
 *   4. Listen to the OS-level prefers-color-scheme media query and switch
 *      automatically if the user has never manually toggled
 *   5. Apply a short CSS transition class so the swap feels smooth rather
 *      than jarring — but only during the toggle, not on every property
 *      change throughout normal page use
 *
 * Storage key : "arctic-theme"   ("dark" | "light")
 * HTML attr   : data-theme on <html id="htmlRoot">
 *
 * No external dependencies — vanilla JS only.
 */

(function themeSystem() {

  // ── Constants ──────────────────────────────────────────────
  const STORAGE_KEY   = "arctic-theme";
  const THEMES        = { DARK: "dark", LIGHT: "light" };
  const TRANSITION_MS = 240;   // must be >= the CSS transition duration

  // ── Grab elements ──────────────────────────────────────────
  const html   = document.getElementById("htmlRoot") || document.documentElement;
  const btn    = document.getElementById("themeToggle");

  // ── Read current theme ─────────────────────────────────────
  // The inline <script> in base.html already set data-theme on <html>
  // before this deferred script runs, so html.dataset.theme is already
  // correct. We just track it here for toggle logic.
  function getTheme() {
    return html.getAttribute("data-theme") || THEMES.DARK;
  }

  // ── Apply theme ────────────────────────────────────────────
  /**
   * applyTheme(theme, animate)
   * Sets data-theme on <html>, saves to localStorage.
   * If animate=true, adds a transition class for TRANSITION_MS then removes it.
   */
  function applyTheme(theme, animate) {
    if (animate) {
      html.classList.add("theme-transitioning");
      setTimeout(() => html.classList.remove("theme-transitioning"), TRANSITION_MS);
    }

    html.setAttribute("data-theme", theme);
    localStorage.setItem(STORAGE_KEY, theme);

    // Update button aria-label for screen readers
    if (btn) {
      btn.setAttribute(
        "aria-label",
        theme === THEMES.DARK ? "Switch to light theme" : "Switch to dark theme"
      );
    }
  }

  // ── Toggle ─────────────────────────────────────────────────
  function toggleTheme() {
    const next = getTheme() === THEMES.DARK ? THEMES.LIGHT : THEMES.DARK;
    applyTheme(next, true);   // animate=true on manual toggle
  }

  // ── Wire button ────────────────────────────────────────────
  if (btn) {
    btn.addEventListener("click", toggleTheme);

    // Also support keyboard: Space and Enter already fire click on <button>,
    // but ensure the button is focusable and styled via :focus-visible in CSS.
  }

  // ── System preference listener ─────────────────────────────
  /**
   * If the user has NEVER manually picked a theme (no localStorage entry),
   * we watch for OS-level theme changes and follow them automatically.
   * Once the user makes a manual choice it's stored and this listener
   * no longer overrides anything.
   */
  const systemDarkQuery = window.matchMedia("(prefers-color-scheme: dark)");

  systemDarkQuery.addEventListener("change", (e) => {
    // Only auto-follow if there is no stored manual preference
    if (!localStorage.getItem(STORAGE_KEY)) {
      applyTheme(e.matches ? THEMES.DARK : THEMES.LIGHT, true);
    }
  });

  // ── Init aria-label on load ────────────────────────────────
  // Set the correct initial aria-label without animating
  applyTheme(getTheme(), false);

})();
