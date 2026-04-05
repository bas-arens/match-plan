// ─────────────────────────────────────────────────────────────────────────────
// File:    src/utils/time.js
// Author:  Bas Arens
// Purpose: Shared time conversion utilities used by GanttChart and
//          TeamPreferences to avoid duplicate implementations.
//
// Exports:
//   timeToMin  — "HH:MM" string → total minutes since midnight (e.g. "09:30" → 570)
//   minToTime  — total minutes → "HH:MM" string (e.g. 570 → "09:30")
// ─────────────────────────────────────────────────────────────────────────────

// Converts a "HH:MM" time string to minutes since midnight.
export function timeToMin(t) {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}

// Converts minutes since midnight to a zero-padded "HH:MM" string.
export function minToTime(min) {
  return `${String(Math.floor(min / 60)).padStart(2, '0')}:${String(min % 60).padStart(2, '0')}`
}
