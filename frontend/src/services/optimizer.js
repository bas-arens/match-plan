import { API_BASE, apiFetch } from './config.js'

export const runOptimizer = date =>
  apiFetch(`${API_BASE}/optimize/run`, {
    method: 'POST',
    body: JSON.stringify({ date }),
  })
