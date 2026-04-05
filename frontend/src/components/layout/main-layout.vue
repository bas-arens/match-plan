<template>
  <div class="flex flex-col min-h-screen">

    <!-- CONTENT (2-column layout) -->
    <div class="flex flex-1">

      <!-- LEFT PANEL -->
      <div class="w-1/2 p-8 bg-gray-50 dark:bg-gray-900 overflow-y-auto border-r border-gray-200 dark:border-gray-800">
        <slot name="left"></slot>
      </div>

      <!-- RIGHT PANEL -->
      <div class="w-1/2 p-8 overflow-y-auto dark:bg-gray-950">
        <slot name="right"></slot>
      </div>

    </div>
  </div>
</template>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// File:    src/components/layout/main-layout.vue
// Author:  Bas Arens
// Purpose: Two-column page layout used by the calendar / home page.
//          Left panel (gray background) for the match list, right panel
//          (white) for the calendar and controls.
//          Slots: #left, #right
// ─────────────────────────────────────────────────────────────────────────────
import Navbar from '@/components/layout/navbar.vue'
</script>
