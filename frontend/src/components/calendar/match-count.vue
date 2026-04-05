<template>
  <div class="p-6 bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 text-center w-full">
    <div class="text-7xl font-extrabold text-gray-900 dark:text-white leading-none">
      {{ count }}
    </div>
    <div class="mt-2 text-xs font-semibold text-gray-400 uppercase tracking-widest">
      {{ count === 1 ? 'wedstrijd' : 'wedstrijden' }}
    </div>
  </div>
</template>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// File:    src/components/calendar/match-count.vue
// Author:  MatchPlan
// Purpose: Displays the number of matches on the selected date as a large
//          bold number with a muted label. Shown below the Plan Matchday button.
//
// Props:
//   count  — number of matches to display (default: 0)
// ─────────────────────────────────────────────────────────────────────────────
defineProps({
  count: { type: Number, default: 0 },
})
</script>
