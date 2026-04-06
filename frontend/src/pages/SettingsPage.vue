<template>
  <div class="p-8 max-w-full mx-auto space-y-6 dark:bg-gray-950 min-h-screen">

    <!-- TABS -->
    <div class="flex gap-8 border-b border-gray-200 dark:border-gray-800">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="activeTab = tab.id"
        class="pb-3 text-sm font-medium transition-colors"
        :class="activeTab === tab.id
          ? 'border-b-2 border-gray-900 dark:border-white text-gray-900 dark:text-white'
          : 'text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- TAB: VELDEN & KLEEDKAMERS -->
    <div v-if="activeTab === 'resources'" class="grid grid-cols-2 gap-12">
      <FieldsSettings />
      <LockerRoomSettings />
    </div>

    <!-- TAB: TIJDVENSTERS -->
    <div v-if="activeTab === 'windows'">
      <TeamPreferences />
    </div>

    <!-- TAB: VASTE SLOTS -->
    <div v-if="activeTab === 'fixed'">
      <FixedSlots />
    </div>

    <!-- TAB: OPTIMIZER -->
    <div v-if="activeTab === 'optimizer'" class="space-y-10">
      <OptimizerSettings />
      <PrioritySettings />
    </div>

  </div>
</template>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// File:    src/pages/SettingsPage.vue
// Author:  Bas Arens
// Purpose: Settings page with three tabs:
//            • Velden & Kleedkamers  — field and locker room configuration
//            • Tijdvensters & Voorkeuren — team time-window and preference config
//            • Optimizer             — algorithm selection
// ─────────────────────────────────────────────────────────────────────────────
import { ref } from 'vue'
import FieldsSettings     from '@/components/settings/Fields.vue'
import LockerRoomSettings from '@/components/settings/Lockerrooms.vue'
import TeamPreferences    from '@/components/settings/TeamPreferences.vue'
import FixedSlots         from '@/components/settings/FixedSlots.vue'
import OptimizerSettings  from '@/components/settings/Optimizer.vue'
import PrioritySettings   from '@/components/settings/Priorities.vue'

const activeTab = ref('resources')

const tabs = [
  { id: 'resources', label: 'Velden & Kleedkamers' },
  { id: 'windows',   label: 'Tijdvensters & Voorkeuren' },
  { id: 'fixed',     label: 'Vaste Slots' },
  { id: 'optimizer', label: 'Optimizer' },
]
</script>
