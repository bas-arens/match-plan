<template>
  <div class="p-4 bg-white rounded shadow text-center w-full h-full flex flex-col justify-center">

    <!-- Count number -->
    <div class="text-8xl font-extrabold text-brand-primary">
      {{ count }}
    </div>

    <!-- Label -->
    <div class="mt-1 text-brand-primaryDark font-semibold">
      {{ count === 1 ? 'wedstrijd' : 'wedstrijden' }}
    </div>

  </div>
</template>

<script setup>
defineProps({
  count: { type: Number, default: 0 },
})
</script>
