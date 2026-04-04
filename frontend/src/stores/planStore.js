import { reactive, watch } from 'vue'

const STORAGE_KEY = 'matchplan_plan'

function load() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : { result: null, date: null }
  } catch {
    return { result: null, date: null }
  }
}

export const planStore = reactive(load())

watch(planStore, val => {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(val))
}, { deep: true })
