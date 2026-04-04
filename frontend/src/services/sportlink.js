import { API_BASE, apiFetch } from './config.js'

const BASE = `${API_BASE}/sportlink`

export const getLogo            = ()     => apiFetch(`${BASE}/logo`)
export const getDatumLijst      = ()     => apiFetch(`${BASE}/programma/datumlijst`)
export const getTeams           = ()     => apiFetch(`${BASE}/teams`)
export const getProgrammaOpDatum = date  => apiFetch(`${BASE}/programma/datum?datum=${date}`)
