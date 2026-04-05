// ─────────────────────────────────────────────────────────────────────────────
// File:    src/services/optimizer.js
// Author:  Bas Arens
// Purpose: Triggers the backend match-planning optimizer for a given date.
//
// Exports:
//   runOptimizer — POST /optimize/run with an ISO date string.
//                  Returns { status, algorithm, scheduled[] } on success,
//                  or { status: 'empty' } when there are no home matches.
// ─────────────────────────────────────────────────────────────────────────────

import { API_BASE, apiFetch } from './config.js'

export const runOptimizer = date =>
  apiFetch(`${API_BASE}/optimize/run`, {
    method: 'POST',
    body: JSON.stringify({ date }),
  })
