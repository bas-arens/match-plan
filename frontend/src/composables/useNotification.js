import { ref } from 'vue'

const notifications = ref([])

export function useNotification() {
  function notify(message, type = 'error') {
    const id = crypto.randomUUID()
    notifications.value.push({ id, message, type })
    setTimeout(() => dismiss(id), 4000)
  }

  function dismiss(id) {
    notifications.value = notifications.value.filter(n => n.id !== id)
  }

  return { notifications, notify, dismiss }
}
