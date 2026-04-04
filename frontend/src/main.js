import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { useNotification } from './composables/useNotification.js'

const app = createApp(App)
app.use(router)

// Global error handler — catches errors from Vue component tree
app.config.errorHandler = (err) => {
  const { notify } = useNotification()
  notify(err?.message ?? 'Er is een onverwachte fout opgetreden.')
}

// Catch unhandled promise rejections (e.g. failed API calls)
window.addEventListener('unhandledrejection', (event) => {
  const { notify } = useNotification()
  notify(event.reason?.message ?? 'Netwerkfout. Probeer het opnieuw.')
  event.preventDefault()
})

app.mount('#app')
