import { API_BASE } from './config.js'

const BASE = `${API_BASE}/sportlink`

export async function getLogo() {
  const r = await fetch(`${BASE}/logo`)
  return r.json()
}

export async function getProgrammaOpDatum(date) {
  const r = await fetch(`${BASE}/programma/datum?datum=${date}`)
  return r.json()
}

export async function getDatumLijst() {
  const r = await fetch(`${BASE}/programma/datumlijst`)
  return r.json()
}

export async function getTeams() {
  const r = await fetch(`${BASE}/teams`)
  return r.json()
}
