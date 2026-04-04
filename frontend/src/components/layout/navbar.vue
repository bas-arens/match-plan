<script setup>
import { RouterLink, useRoute } from 'vue-router'
import { ref, onMounted } from 'vue'
import { Sun, Moon } from 'lucide-vue-next'
import { useTheme } from '@/composables/useTheme.js'
import { getLogo } from '@/services/sportlink.js'

const route = useRoute()
const isActive = (path) => route.path === path

const activeClass = 'bg-gray-700 text-white'
const defaultClass = 'text-gray-400 hover:bg-gray-800 hover:text-white'

const { isDark, toggleTheme } = useTheme()

// --- Dynamic logo from backend ---
const logoUrl = ref(null)

onMounted(async () => {
  try {
    const data = await getLogo()
    logoUrl.value = data.logo
  } catch {
    // no logo available — fallback shown in template
  }
})
</script>

<template>
  <nav class="bg-gray-900 border-b border-gray-800">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="flex h-20 items-center justify-between">

        <!-- LEFT: Club Logo + App Name -->
        <RouterLink to="/" class="flex items-center flex-shrink-0">
          <img
            v-if="logoUrl"
            :src="logoUrl"
            class="h-10 w-auto rounded"
            alt="Club Logo"
          />
          <div
            v-else
            class="h-10 w-10 bg-gray-700 rounded flex items-center justify-center text-white font-bold text-sm"
          >
            MP
          </div>
          <span class="text-white text-2xl font-bold ml-2">MatchPlan</span>
        </RouterLink>

        <!-- RIGHT: Navigation Links + Theme Toggle -->
        <div class="flex items-center space-x-2">

          <RouterLink
            to="/calendar"
            :class="[isActive('/calendar') ? activeClass : defaultClass, 'px-3 py-2 rounded-md font-medium text-sm']"
          >
            Kalender
          </RouterLink>

          <RouterLink
            to="/settings"
            :class="[isActive('/settings') ? activeClass : defaultClass, 'px-3 py-2 rounded-md font-medium text-sm']"
          >
            Instellingen
          </RouterLink>

          <RouterLink
            to="/matchplan"
            :class="[isActive('/matchplan') ? activeClass : defaultClass, 'px-3 py-2 rounded-md font-medium text-sm']"
          >
            MatchPlan
          </RouterLink>

          <!-- THEME TOGGLE -->
          <button
            @click="toggleTheme"
            class="ml-3 p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
            :title="isDark ? 'Licht thema' : 'Donker thema'"
          >
            <Sun v-if="isDark" :size="16" />
            <Moon v-else :size="16" />
          </button>

        </div>
      </div>
    </div>
  </nav>
</template>
