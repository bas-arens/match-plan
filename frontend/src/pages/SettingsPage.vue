<template>
  <div class="p-8 space-y-8 max-w-7xl mx-auto">

    <h1 class="text-2xl font-bold text-brand-dark">Instellingen</h1>

    <!-- 1. Resources -->
    <div class="grid grid-cols-2 gap-6">

      <!-- Velden -->
      <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
        <FieldsSettings />
      </div>

      <!-- Kleedkamers -->
      <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
        <LockerRoomSettings />
      </div>

    </div>

    <!-- 2. Team Preferences -->
    <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
      <TeamPreferences />
    </div>

    <!-- 3. Optimizer Settings -->
    <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-200 max-w-sm">
      <OptimizerSettings />
    </div>

  </div>
</template>

<script setup>
import FieldsSettings from '@/components/settings/Fields.vue'
import LockerRoomSettings from '@/components/settings/Lockerrooms.vue'
import TeamPreferences from '@/components/settings/TeamPreferences.vue'
import OptimizerSettings from '@/components/settings/Optimizer.vue'
</script>
