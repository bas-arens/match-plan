<template>
  <div class="min-h-screen bg-white dark:bg-gray-950 transition-colors duration-200">
    <Navbar v-if="showNav" />
    <router-view />
    <Toast />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from '@/components/layout/navbar.vue'
import Toast  from '@/components/common/Toast.vue'
import '@/composables/useTheme.js'

const route   = useRoute()
const showNav = computed(() => route.path !== '/login')
</script>
