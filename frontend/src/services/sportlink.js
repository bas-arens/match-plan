// ─────────────────────────────────────────────────────────────────────────────
// File:    src/services/sportlink.js
// Author:  MatchPlan
// Purpose: API calls to the Sportlink proxy endpoints on the backend.
//          Sportlink is the Dutch sports administration platform that provides
//          match schedules, team data, and club information.
//
// Exports:
//   getLogo              — club logo URL (used in the navbar)
//   getDatumLijst        — list of ISO dates on which the club plays at home
//   getTeams             — teams grouped by category (used in preferences)
//   getProgrammaOpDatum  — all home matches on a given ISO date
// ─────────────────────────────────────────────────────────────────────────────

import { API_BASE, apiFetch } from './config.js'

const BASE = `${API_BASE}/sportlink`

export const getLogo             = ()    => apiFetch(`${BASE}/logo`)
export const getDatumLijst       = ()    => apiFetch(`${BASE}/programma/datumlijst`)
export const getTeams            = ()    => apiFetch(`${BASE}/teams`)
export const getProgrammaOpDatum = date  => apiFetch(`${BASE}/programma/datum?datum=${date}`)
