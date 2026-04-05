<template>
  <div class="min-h-screen bg-white dark:bg-gray-950 transition-colors duration-200">
    <Navbar v-if="showNav" />
    <router-view />
    <Toast />
  </div>
</template>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// File:    src/App.vue
// Author:  MatchPlan
// Purpose: Root application component. Renders the navbar (hidden on /login),
//          the current route view, and the global Toast notification overlay.
// ─────────────────────────────────────────────────────────────────────────────
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from '@/components/layout/navbar.vue'
import Toast  from '@/components/common/Toast.vue'
import '@/composables/useTheme.js'

const route   = useRoute()
const showNav = computed(() => route.path !== '/login')
</script>
