// ─────────────────────────────────────────────────────────────────────────────
// File:    src/services/settings.js
// Author:  MatchPlan
// Purpose: API calls for club-specific configuration stored in the backend.
//          All functions use apiFetch, which handles auth headers and throws
//          on HTTP errors.
//
// Exports:
//   getFields        — fetch all configured fields
//   saveFields       — overwrite all fields
//   getLockers       — fetch all configured locker rooms
//   saveLockers      — overwrite all locker rooms
//   getPreferences   — fetch team time-window and field/locker preferences
//   savePreferences  — overwrite all team preferences
//   getOptimizer     — fetch currently selected optimizer algorithm
//   saveOptimizer    — persist selected algorithm
// ─────────────────────────────────────────────────────────────────────────────

import { API_BASE, apiFetch } from './config.js'

const BASE = `${API_BASE}/settings`

export const getFields      = ()        => apiFetch(`${BASE}/fields`)
export const getLockers     = ()        => apiFetch(`${BASE}/lockers`)
export const getPreferences = ()        => apiFetch(`${BASE}/preferences`)
export const getOptimizer   = ()        => apiFetch(`${BASE}/optimizer`)

export const saveFields      = fields      => apiFetch(`${BASE}/fields`,      { method: 'POST', body: JSON.stringify(fields) })
export const saveLockers     = lockers     => apiFetch(`${BASE}/lockers`,     { method: 'POST', body: JSON.stringify(lockers) })
export const savePreferences = preferences => apiFetch(`${BASE}/preferences`, { method: 'POST', body: JSON.stringify(preferences) })
export const saveOptimizer   = settings    => apiFetch(`${BASE}/optimizer`,   { method: 'POST', body: JSON.stringify(settings) })
