import { authStore } from '@/stores/authStore.js'

export const API_BASE = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

export async function apiFetch(url, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (authStore.token) headers['Authorization'] = `Bearer ${authStore.token}`

  const res = await fetch(url, { ...options, headers })
  if (!res.ok) throw new Error(`API fout ${res.status}: ${res.statusText}`)
  return res.json()
}
