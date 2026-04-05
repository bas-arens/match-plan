// ─────────────────────────────────────────────────────────────────────────────
// File:    src/composables/useTheme.js
// Author:  Bas Arens
// Purpose: Composable that manages the dark / light theme toggle.
//          The chosen theme is stored in localStorage and applied immediately
//          on import by adding or removing the "dark" class on <html>.
//
// Exports:
//   useTheme()  → { isDark, toggleTheme }
//     isDark       — ref<boolean> reflecting current theme
//     toggleTheme  — flips the theme and persists the choice
// ─────────────────────────────────────────────────────────────────────────────

import { ref, watch } from 'vue'

const isDark = ref(localStorage.getItem('theme') === 'dark')

// Sync the "dark" class on <html> with the current state.
function applyTheme() {
  document.documentElement.classList.toggle('dark', isDark.value)
}

export function toggleTheme() {
  isDark.value = !isDark.value
}

// Persist and apply whenever the value changes.
watch(isDark, (val) => {
  localStorage.setItem('theme', val ? 'dark' : 'light')
  applyTheme()
})

// Apply on module load so the correct theme is set before first render,
// preventing a flash of the wrong theme.
applyTheme()

export function useTheme() {
  return { isDark, toggleTheme }
}
