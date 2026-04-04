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
