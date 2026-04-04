import { reactive } from 'vue'

export const planStore = reactive({
  result: null,   // full API response: { status, algorithm, date, scheduled }
  date: null,     // ISO string e.g. "2026-04-05"
})
