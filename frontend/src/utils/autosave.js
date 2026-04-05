// ─────────────────────────────────────────────────────────────────────────────
// File:    src/utils/autosave.js
// Author:  MatchPlan
// Purpose: Debounced auto-save helper. Prevents flooding the backend with a
//          save request on every keystroke or checkbox toggle.
//          Each unique key gets its own independent timer.
//
// Exports:
//   autosave(key, callback, delay?)
//     key       — identifier for the timer (e.g. 'fields', 'preferences')
//     callback  — async function to call after the delay
//     delay     — debounce delay in ms (default: 600)
// ─────────────────────────────────────────────────────────────────────────────

// One timer slot per save key.
const timers = {}

export function autosave(key, callback, delay = 600) {
  // Cancel any pending save for this key before starting a new countdown.
  clearTimeout(timers[key])
  timers[key] = setTimeout(callback, delay)
}
