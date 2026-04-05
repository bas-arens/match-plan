// ─────────────────────────────────────────────────────────────────────────────
// File:    src/services/config.js
// Author:  Bas Arens
// Purpose: Central API configuration and authenticated fetch wrapper.
//          All service files import from here so the base URL and auth header
//          logic live in exactly one place.
//
// Exports:
//   API_BASE   — backend base URL read from VITE_API_URL (.env), with a
//                fallback to localhost for local development
//   apiFetch   — drop-in fetch wrapper that:
//                  • adds Content-Type: application/json
//                  • attaches Bearer token when the user is logged in
//                  • throws an Error on non-2xx HTTP responses
// ─────────────────────────────────────────────────────────────────────────────

import { authStore } from '@/stores/authStore.js'

export const API_BASE = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

export async function apiFetch(url, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers }

  // Attach JWT when the user has an active session.
  if (authStore.token) headers['Authorization'] = `Bearer ${authStore.token}`

  const res = await fetch(url, { ...options, headers })

  // Throw so callers and the global error handler can surface the problem.
  if (!res.ok) throw new Error(`API fout ${res.status}: ${res.statusText}`)

  return res.json()
}
