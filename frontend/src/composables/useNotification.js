// ─────────────────────────────────────────────────────────────────────────────
// File:    src/composables/useNotification.js
// Author:  MatchPlan
// Purpose: Global notification queue used to display toast messages.
//          The notifications array is module-level so all components share
//          the same queue — only one Toast component is needed in App.vue.
//
// Exports:
//   useNotification()  → { notifications, notify, dismiss }
//     notifications  — ref<array> of active { id, message, type } objects
//     notify         — push a new toast (auto-dismissed after 4 seconds)
//     dismiss        — remove a toast by id immediately
// ─────────────────────────────────────────────────────────────────────────────

import { ref } from 'vue'

// Shared state — all callers read from and write to the same array.
const notifications = ref([])

export function useNotification() {
  function notify(message, type = 'error') {
    const id = crypto.randomUUID()
    notifications.value.push({ id, message, type })
    // Auto-dismiss after 4 seconds.
    setTimeout(() => dismiss(id), 4000)
  }

  function dismiss(id) {
    notifications.value = notifications.value.filter(n => n.id !== id)
  }

  return { notifications, notify, dismiss }
}
