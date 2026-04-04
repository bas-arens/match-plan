import { reactive } from 'vue'

function load() {
  try {
    const raw = localStorage.getItem('matchplan_auth')
    return raw ? JSON.parse(raw) : { token: null, user: null }
  } catch {
    return { token: null, user: null }
  }
}

export const authStore = reactive(load())

export function setAuth(token, user) {
  authStore.token = token
  authStore.user  = user
  localStorage.setItem('matchplan_auth', JSON.stringify({ token, user }))
}

export function clearAuth() {
  authStore.token = null
  authStore.user  = null
  localStorage.removeItem('matchplan_auth')
}
