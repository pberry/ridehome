/**
 * Theme Toggle for Solarized Light/Dark
 * Persists preference in localStorage
 */

(function() {
  'use strict';

  const STORAGE_KEY = 'theme-preference';
  const THEME_LIGHT = 'light';
  const THEME_DARK = 'dark';

  // Get saved theme or default to light
  function getSavedTheme() {
    return localStorage.getItem(STORAGE_KEY) || THEME_LIGHT;
  }

  // Apply theme to document
  function applyTheme(theme) {
    if (theme === THEME_DARK) {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
  }

  // Update toggle button icon and ARIA state
  function updateToggleButton(theme) {
    const icon = document.querySelector('.theme-toggle-icon');
    if (icon) {
      icon.textContent = theme === THEME_DARK ? '🌙' : '☀️';
    }

    const button = document.getElementById('theme-toggle');
    if (button) {
      button.setAttribute('aria-label',
        theme === THEME_DARK ? 'Switch to light mode' : 'Switch to dark mode'
      );
      // Add aria-pressed to indicate toggle state
      button.setAttribute('aria-pressed', theme === THEME_DARK ? 'true' : 'false');
    }
  }

  // Toggle between themes
  function toggleTheme() {
    const currentTheme = getSavedTheme();
    const newTheme = currentTheme === THEME_LIGHT ? THEME_DARK : THEME_LIGHT;

    localStorage.setItem(STORAGE_KEY, newTheme);
    applyTheme(newTheme);
    updateToggleButton(newTheme);
  }

  // Initialize theme on page load
  function initTheme() {
    const savedTheme = getSavedTheme();
    applyTheme(savedTheme);
    updateToggleButton(savedTheme);

    // Add click handler to toggle button
    const toggleButton = document.getElementById('theme-toggle');
    if (toggleButton) {
      toggleButton.addEventListener('click', toggleTheme);
    }
  }

  // Apply theme immediately to prevent flash
  applyTheme(getSavedTheme());

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTheme);
  } else {
    initTheme();
  }
})();
