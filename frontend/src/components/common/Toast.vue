<template>
  <Teleport to="body">
    <div class="fixed bottom-6 right-6 z-[9999] flex flex-col gap-2 pointer-events-none">
      <transition-group name="toast">
        <div
          v-for="n in notifications"
          :key="n.id"
          class="pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-xl shadow-lg text-sm font-medium max-w-sm"
          :class="n.type === 'error'
            ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'
            : 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'"
        >
          <span class="leading-relaxed">{{ n.message }}</span>
          <button
            @click="dismiss(n.id)"
            class="ml-auto text-gray-400 hover:text-white dark:hover:text-gray-700 shrink-0"
          >✕</button>
        </div>
      </transition-group>
    </div>
  </Teleport>
</template>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// File:    src/components/common/Toast.vue
// Author:  Bas Arens
// Purpose: Global toast notification overlay. Mounted once in App.vue via a
//          Teleport to <body>. Reads from the shared useNotification queue —
//          any component can push a message with notify() and it appears here.
//          Toasts animate in from below and slide out to the right on dismiss.
// ─────────────────────────────────────────────────────────────────────────────
import { useNotification } from '@/composables/useNotification.js'
const { notifications, dismiss } = useNotification()
</script>

<style scoped>
.toast-enter-from  { opacity: 0; transform: translateY(8px); }
.toast-enter-to    { opacity: 1; transform: translateY(0); }
.toast-leave-to    { opacity: 0; transform: translateX(16px); }
.toast-enter-active, .toast-leave-active { transition: all 0.2s ease; }
</style>
