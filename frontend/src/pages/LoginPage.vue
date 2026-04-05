<template>
  <div class="min-h-screen bg-white dark:bg-gray-950 flex items-center justify-center px-4">
    <div class="w-full max-w-sm">

      <!-- BRAND -->
      <div class="mb-8 text-center">
        <div class="inline-flex items-center justify-center w-12 h-12 bg-gray-900 dark:bg-white rounded-xl mb-4">
          <span class="text-white dark:text-gray-900 font-bold text-lg">MP</span>
        </div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">MatchPlan</h1>
        <p class="text-sm text-gray-400 mt-1">Inloggen bij jouw club</p>
      </div>

      <!-- FORM -->
      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1.5">
            E-mailadres
          </label>
          <input
            v-model="email"
            type="email"
            required
            autocomplete="email"
            class="w-full px-3 py-2.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:outline-none focus:border-gray-400 dark:focus:border-gray-500 transition-colors"
          />
        </div>

        <div>
          <label class="block text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1.5">
            Wachtwoord
          </label>
          <input
            v-model="password"
            type="password"
            required
            autocomplete="current-password"
            class="w-full px-3 py-2.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:outline-none focus:border-gray-400 dark:focus:border-gray-500 transition-colors"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-semibold py-2.5 rounded-lg text-sm hover:bg-gray-700 dark:hover:bg-gray-100 transition-colors disabled:opacity-50 flex items-center justify-center gap-2 mt-2"
        >
          <Loader2 v-if="loading" :size="15" class="animate-spin" />
          <span>{{ loading ? 'Inloggen...' : 'Inloggen' }}</span>
        </button>
      </form>

      <p v-if="error" class="mt-4 text-sm text-red-500 text-center">{{ error }}</p>

    </div>
  </div>
</template>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// File:    src/pages/LoginPage.vue
// Author:  Bas Arens
// Purpose: Login page — email/password form that calls POST /auth/login.
//          On success, persists the JWT token via setAuth() and navigates
//          to the calendar. Shown without the navbar.
//
// Functions:
//   handleLogin  — submits credentials, stores token, redirects on success
// ─────────────────────────────────────────────────────────────────────────────
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Loader2 } from 'lucide-vue-next'
import { setAuth } from '@/stores/authStore.js'
import { API_BASE } from '@/services/config.js'

const router   = useRouter()
const email    = ref('')
const password = ref('')
const loading  = ref(false)
const error    = ref(null)

async function handleLogin() {
  loading.value = true
  error.value   = null
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email: email.value, password: password.value }),
    })
    if (!res.ok) throw new Error('Verkeerd e-mailadres of wachtwoord.')
    const { token, user } = await res.json()
    setAuth(token, user)
    router.push('/calendar')
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}
</script>
