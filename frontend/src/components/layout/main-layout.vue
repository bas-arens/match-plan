<template>
  <div class="flex flex-col min-h-screen">

    <!-- CONTENT (2-column layout) -->
    <div class="flex flex-1">

      <!-- LEFT PANEL -->
      <div class="w-1/2 p-8 bg-gray-50 overflow-y-auto border-r border-gray-200">
        <slot name="left"></slot>
      </div>

      <!-- RIGHT PANEL -->
      <div class="w-1/2 p-8 overflow-y-auto">
        <slot name="right"></slot>
      </div>

    </div>
  </div>
</template>

<script setup>
import Navbar from '@/components/layout/navbar.vue'
</script>
