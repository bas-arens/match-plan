<template>
  <div class="max-w-2xl space-y-3">

    <h2 class="text-sm font-bold uppercase tracking-widest text-gray-400 mb-6">Prioriteiten</h2>

    <p class="text-xs text-gray-500 leading-relaxed mb-4">
      Geef aan wat voor jouw club het belangrijkst is. De planner weegt deze voorkeuren mee bij het maken van de planning.
    </p>

    <div
      v-for="item in items"
      :key="item.key"
      class="p-4 border rounded border-gray-100 space-y-3"
    >
      <div class="flex items-center justify-between">
        <span class="font-bold text-sm text-gray-800">{{ item.label }}</span>
        <span
          class="text-xs px-2 py-0.5 rounded border font-medium"
          :class="badgeClass(priorities[item.key])"
        >{{ badgeLabel(priorities[item.key]) }}</span>
      </div>
      <p class="text-xs text-gray-400">{{ item.description }}</p>
      <div class="flex items-center gap-3">
        <button
          v-for="level in levels"
          :key="level.value"
          @click="set(item.key, level.value)"
          class="flex-1 py-2 text-xs font-semibold rounded-lg border-2 transition-all"
          :class="priorities[item.key] === level.value
            ? `${level.activeClass} shadow-sm`
            : 'border-gray-200 text-gray-400 hover:border-gray-300'"
        >
          {{ level.label }}
        </button>
      </div>
    </div>

  </div>
</template>

<script setup>
import { reactive, onMounted } from 'vue'
import { getPriorities, savePriorities } from '@/services/settings'
import { autosave } from '@/utils/autosave'

const priorities = reactive({
  lockers: 1,
  time_windows: 1,
  field_preference: 1,
})

const items = [
  {
    key: 'lockers',
    label: 'Kleedkamers',
    description: 'Hoe belangrijk is het dat teams hun eigen kleedkamer hebben en niet hoeven te delen?',
  },
  {
    key: 'time_windows',
    label: 'Tijdvensters',
    description: 'Hoe strikt moeten de opgegeven speeltijden worden aangehouden?',
  },
  {
    key: 'field_preference',
    label: 'Veldvoorkeur',
    description: 'Hoe belangrijk is het dat teams op hun voorkeursveld spelen?',
  },
]

const levels = [
  { value: 0, label: 'Niet belangrijk', activeClass: 'border-gray-400 text-gray-600 bg-gray-50' },
  { value: 1, label: 'Normaal',         activeClass: 'border-blue-500 text-blue-600 bg-blue-50' },
  { value: 2, label: 'Heel belangrijk', activeClass: 'border-orange-500 text-orange-600 bg-orange-50' },
]

function badgeClass(value) {
  if (value === 0) return 'border-gray-200 text-gray-500 bg-gray-50'
  if (value === 2) return 'border-orange-200 text-orange-700 bg-orange-50'
  return 'border-blue-200 text-blue-700 bg-blue-50'
}

function badgeLabel(value) {
  return levels.find(l => l.value === value)?.label ?? 'Normaal'
}

onMounted(async () => {
  const data = await getPriorities()
  Object.assign(priorities, data)
})

function set(key, value) {
  priorities[key] = value
  autosave('priorities', async () => {
    await savePriorities({ ...priorities })
  })
}
</script>
