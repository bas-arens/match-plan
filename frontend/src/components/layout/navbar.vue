<script setup>
import { RouterLink, useRoute } from 'vue-router'
import { ref, onMounted } from 'vue'
import FieldIcon from '@/assets/field.svg'


// --- Active route handling ---
const route = useRoute()
const isActive = (path) => route.path === path

// New centralized Tailwind brand colors
const activeClass = 'bg-gray-700 text-white'
const defaultClass = 'text-gray-400 hover:bg-gray-800 hover:text-white'

// --- Dynamic logo from backend ---
const logoUrl = ref(null)

onMounted(async () => {
  try {
    const res = await fetch("http://localhost:8000/sportlink/logo")
    const data = await res.json()
    logoUrl.value = data.logo
  } catch (err) {
    console.error("Failed to load club logo:", err)
  }
})
</script>

<template>
  <nav class="bg-gray-900 border-b border-gray-800">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="flex h-20 items-center justify-between">

        <!-- LEFT: Club Logo + App Name -->
        <RouterLink to="/" class="flex items-center flex-shrink-0">

          <!-- Dynamic club logo -->
          <img
            v-if="logoUrl"
            :src="logoUrl"
            class="h-10 w-auto rounded"
            alt="Club Logo"
          />

          <!-- Fallback if no logo loaded -->
          <div
            v-else
            class="h-10 w-10 bg-gray-900 rounded flex items-center justify-center text-white font-bold"
          >
            MP
          </div>

          <!-- App name -->
          <span class="text-white text-2xl font-bold ml-2">
            MatchPlan
          </span>
        </RouterLink>

        <!-- RIGHT: Navigation Links -->
        <div class="flex space-x-2">

          <RouterLink
            to="/calendar"
            :class="[
              isActive('/calendar') ? activeClass : defaultClass,
              'px-3 py-2 rounded-md font-medium'
            ]"
          >
            Kalender
          </RouterLink>

          <RouterLink
            to="/settings"
            :class="[
              isActive('/settings') ? activeClass : defaultClass,
              'px-3 py-2 rounded-md font-medium'
            ]"
          >
            Instellingen
          </RouterLink>

          <RouterLink
            to="/matchplan"
            :class="[
              isActive('/matchplan') ? activeClass : defaultClass,
              'px-3 py-2 rounded-md font-medium'
            ]"
          >
            MatchPlan
          </RouterLink>

          <!-- FIELD ICON BUTTON -->
          <button class="ml-4">
            <img :src="FieldIcon" alt="veld icon" class="h-7 w-7 opacity-90 hover:opacity-100" />
          </button>

        </div>
      </div>
    </div>
  </nav>
</template>
