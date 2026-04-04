import { ref, watch } from 'vue'

const isDark = ref(localStorage.getItem('theme') === 'dark')

function applyTheme() {
  document.documentElement.classList.toggle('dark', isDark.value)
}

function toggleTheme() {
  isDark.value = !isDark.value
}

watch(isDark, (val) => {
  localStorage.setItem('theme', val ? 'dark' : 'light')
  applyTheme()
})

// Apply on module load so the correct theme is set before first render
applyTheme()

export function useTheme() {
  return { isDark, toggleTheme }
}
