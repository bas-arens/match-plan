import { API_BASE } from './config.js'

const BASE = `${API_BASE}/settings`

export async function getFields() {
  const res = await fetch(`${BASE}/fields`)
  return res.json()
}

export async function saveFields(fields) {
  await fetch(`${BASE}/fields`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(fields),
  })
}

export async function getLockers() {
  const res = await fetch(`${BASE}/lockers`)
  return res.json()
}

export async function saveLockers(lockers) {
  await fetch(`${BASE}/lockers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(lockers),
  })
}

export async function getPreferences() {
  const res = await fetch(`${BASE}/preferences`)
  return res.json()
}

export async function savePreferences(preferences) {
  await fetch(`${BASE}/preferences`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(preferences),
  })
}

export async function getOptimizer() {
  const res = await fetch(`${BASE}/optimizer`)
  return res.json()
}

export async function saveOptimizer(settings) {
  await fetch(`${BASE}/optimizer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  })
}
