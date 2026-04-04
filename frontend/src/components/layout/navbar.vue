<script setup>
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { ref, onMounted } from 'vue'
import { Sun, Moon, LogOut } from 'lucide-vue-next'
import { useTheme } from '@/composables/useTheme.js'
import { getLogo } from '@/services/sportlink.js'
import { authStore, clearAuth } from '@/stores/authStore.js'

const route  = useRoute()
const router = useRouter()
const isActive = (path) => route.path === path

const activeClass  = 'bg-gray-700 text-white'
const defaultClass = 'text-gray-400 hover:bg-gray-800 hover:text-white'

const { isDark, toggleTheme } = useTheme()

const logoUrl = ref(null)

onMounted(async () => {
  try {
    const data = await getLogo()
    logoUrl.value = data.logo
  } catch {
    // no logo available — fallback shown in template
  }
})

function logout() {
  clearAuth()
  router.push('/login')
}
</script>

<template>
  <nav class="bg-gray-900 border-b border-gray-800">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="flex h-20 items-center justify-between">

        <!-- LEFT: Club Logo + App Name -->
        <RouterLink to="/" class="flex items-center flex-shrink-0">
          <img v-if="logoUrl" :src="logoUrl" class="h-10 w-auto rounded" alt="Club Logo" />
          <div v-else class="h-10 w-10 bg-gray-700 rounded flex items-center justify-center text-white font-bold text-sm">
            MP
          </div>
          <span class="text-white text-2xl font-bold ml-2">MatchPlan</span>
        </RouterLink>

        <!-- RIGHT: Nav + Theme + Logout -->
        <div class="flex items-center space-x-2">

          <RouterLink to="/calendar"  :class="[isActive('/calendar')  ? activeClass : defaultClass, 'px-3 py-2 rounded-md font-medium text-sm']">Kalender</RouterLink>
          <RouterLink to="/settings"  :class="[isActive('/settings')  ? activeClass : defaultClass, 'px-3 py-2 rounded-md font-medium text-sm']">Instellingen</RouterLink>
          <RouterLink to="/matchplan" :class="[isActive('/matchplan') ? activeClass : defaultClass, 'px-3 py-2 rounded-md font-medium text-sm']">MatchPlan</RouterLink>

          <!-- USER INFO -->
          <span v-if="authStore.user" class="ml-3 text-xs text-gray-500 hidden sm:block">
            {{ authStore.user.email }}
          </span>

          <!-- THEME TOGGLE -->
          <button
            @click="toggleTheme"
            class="ml-2 p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
            :title="isDark ? 'Licht thema' : 'Donker thema'"
          >
            <Sun v-if="isDark" :size="16" />
            <Moon v-else :size="16" />
          </button>

          <!-- LOGOUT (only when authenticated) -->
          <button
            v-if="authStore.token"
            @click="logout"
            class="p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
            title="Uitloggen"
          >
            <LogOut :size="16" />
          </button>

        </div>
      </div>
    </div>
  </nav>
</template>
