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
defineProps({
  count: { type: Number, default: 0 },
})
</script>
