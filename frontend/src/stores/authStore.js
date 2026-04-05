// ─────────────────────────────────────────────────────────────────────────────
// File:    src/stores/authStore.js
// Author:  MatchPlan
// Purpose: Reactive store for the authenticated user's session.
//          Persisted to localStorage so the session survives a page refresh.
//
// Exports:
//   authStore  — reactive object { token, user }
//   setAuth    — persist token + user after a successful login
//   clearAuth  — wipe session on logout
// ─────────────────────────────────────────────────────────────────────────────

import { reactive } from 'vue'

// Restore session from localStorage on app load.
function load() {
  try {
    const raw = localStorage.getItem('matchplan_auth')
    return raw ? JSON.parse(raw) : { token: null, user: null }
  } catch {
    return { token: null, user: null }
  }
}

export const authStore = reactive(load())

// Called after a successful POST /auth/login response.
export function setAuth(token, user) {
  authStore.token = token
  authStore.user  = user
  localStorage.setItem('matchplan_auth', JSON.stringify({ token, user }))
}

// Called on logout — clears both in-memory state and localStorage.
export function clearAuth() {
  authStore.token = null
  authStore.user  = null
  localStorage.removeItem('matchplan_auth')
}
