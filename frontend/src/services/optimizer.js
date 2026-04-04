import { API_BASE } from './config.js'

export async function runOptimizer(date) {
  const res = await fetch(`${API_BASE}/optimize/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ date }),
  })
  return res.json()
}
