<template>
  <div class="min-h-screen bg-white dark:bg-gray-950 flex items-center justify-center px-4">
    <div class="text-center">
      <div class="text-8xl font-extrabold text-gray-900 dark:text-white leading-none">404</div>
      <div class="mt-3 text-xs font-semibold text-gray-400 uppercase tracking-widest">Pagina niet gevonden</div>
      <RouterLink
        to="/"
        class="mt-8 inline-block text-sm text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
      >
        ← terug naar kalender
      </RouterLink>
    </div>
  </div>
</template>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// File:    src/pages/NotFoundPage.vue
// Author:  MatchPlan
// Purpose: Catch-all 404 page rendered for any route that does not match a
//          defined path. Provides a link back to the calendar.
// ─────────────────────────────────────────────────────────────────────────────
import { RouterLink } from 'vue-router'
</script>
