<template>
  <div class="p-8 max-w-6xl mx-auto space-y-6">

    <!-- TABS -->
    <div class="flex gap-8 border-b border-gray-200">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="activeTab = tab.id"
        class="pb-3 text-sm font-medium transition-colors"
        :class="activeTab === tab.id
          ? 'border-b-2 border-gray-900 text-gray-900'
          : 'text-gray-400 hover:text-gray-700'"
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

    <!-- TAB: OPTIMIZER -->
    <div v-if="activeTab === 'optimizer'">
      <OptimizerSettings />
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import FieldsSettings     from '@/components/settings/Fields.vue'
import LockerRoomSettings from '@/components/settings/Lockerrooms.vue'
import TeamPreferences    from '@/components/settings/TeamPreferences.vue'
import OptimizerSettings  from '@/components/settings/Optimizer.vue'

const activeTab = ref('resources')

const tabs = [
  { id: 'resources', label: 'Velden & Kleedkamers' },
  { id: 'windows',   label: 'Tijdvensters & Voorkeuren' },
  { id: 'optimizer', label: 'Optimizer' },
]
</script>
