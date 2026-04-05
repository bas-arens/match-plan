// ─────────────────────────────────────────────────────────────────────────────
// File:    src/main.js
// Author:  MatchPlan
// Purpose: Application entry point — mounts the Vue app and registers
//          global error handlers so unhandled API/runtime errors show a toast.
// ─────────────────────────────────────────────────────────────────────────────

import './assets/main.css'

import { createApp } from 'vue'
import App    from './App.vue'
import router from './router'
import { useNotification } from './composables/useNotification.js'

const app = createApp(App)
app.use(router)

// Catches errors thrown inside Vue component lifecycle hooks and event handlers.
app.config.errorHandler = (err) => {
  const { notify } = useNotification()
  notify(err?.message ?? 'Er is een onverwachte fout opgetreden.')
}

// Catches unhandled promise rejections — e.g. a failed apiFetch that no
// component wrapped in try/catch.
window.addEventListener('unhandledrejection', (event) => {
  const { notify } = useNotification()
  notify(event.reason?.message ?? 'Netwerkfout. Probeer het opnieuw.')
  event.preventDefault()
})

app.mount('#app')
