<template>
  <div class="min-h-screen bg-white dark:bg-gray-950 transition-colors duration-200">
    <Navbar />
    <router-view />
  </div>
</template>

<script setup>
import Navbar from '@/components/layout/navbar.vue'
import '@/composables/useTheme.js'
</script>
