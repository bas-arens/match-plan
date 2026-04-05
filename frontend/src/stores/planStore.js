// ─────────────────────────────────────────────────────────────────────────────
// File:    src/stores/planStore.js
// Author:  Bas Arens
// Purpose: Reactive store for the most recently generated match planning result.
//          Persisted to sessionStorage so a hard-refresh on /matchplan does not
//          lose the planning. Cleared automatically when the browser tab closes.
//
// Shape:
//   result  — full API response { status, algorithm, scheduled[] }
//   date    — ISO date string the planning was generated for (e.g. "2026-04-11")
// ─────────────────────────────────────────────────────────────────────────────

import { reactive, watch } from 'vue'

const STORAGE_KEY = 'matchplan_plan'

// Restore previous state from sessionStorage on page load.
function load() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : { result: null, date: null }
  } catch {
    return { result: null, date: null }
  }
}

export const planStore = reactive(load())

// Keep sessionStorage in sync whenever the store changes.
watch(planStore, val => {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(val))
}, { deep: true })
