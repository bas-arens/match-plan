<template>
  <div class="max-w-2xl space-y-3">

    <h2 class="text-sm font-bold uppercase tracking-widest text-gray-400 mb-6">Algoritme</h2>

    <div
      v-for="option in algorithms"
      :key="option.value"
      @click="select(option.value)"
      class="flex gap-4 p-4 border rounded cursor-pointer transition-colors"
      :class="algo === option.value
        ? 'border-gray-800 bg-gray-50'
        : 'border-gray-100 hover:border-gray-300'"
    >
      <!-- Radio dot -->
      <div class="mt-0.5 flex-shrink-0">
        <div
          class="w-3.5 h-3.5 rounded-full border-2 flex items-center justify-center transition-colors"
          :class="algo === option.value ? 'border-gray-800' : 'border-gray-300'"
        >
          <div
            v-if="algo === option.value"
            class="w-1.5 h-1.5 rounded-full bg-gray-800"
          />
        </div>
      </div>

      <!-- Content -->
      <div class="space-y-1.5">
        <div class="flex items-center gap-3">
          <span class="font-bold text-sm text-gray-800">{{ option.label }}</span>
          <span
            class="text-xs px-2 py-0.5 rounded border font-medium"
            :class="option.badgeClass"
          >{{ option.badge }}</span>
        </div>
        <p class="text-xs text-gray-500 leading-relaxed">{{ option.description }}</p>
        <p class="text-xs text-gray-400">
          <span class="font-medium text-gray-500">Gebruik wanneer: </span>{{ option.when }}
        </p>
      </div>
    </div>

  </div>
</template>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// File:    src/components/settings/Optimizer.vue
// Author:  MatchPlan
// Purpose: Algorithm selection panel — shows clickable cards for Greedy,
//          Simulated Annealing, and MILP with plain-language descriptions
//          using football analogies. Selection is auto-saved.
//
// Functions:
//   select  — updates the selected algorithm and triggers a debounced save
// ─────────────────────────────────────────────────────────────────────────────
import { ref, onMounted } from 'vue'
import { getOptimizer, saveOptimizer } from '@/services/settings'
import { autosave } from '@/utils/autosave'

const algo = ref('sa')

const algorithms = [
  {
    value: 'greedy',
    label: 'Greedy',
    badge: 'snel',
    badgeClass: 'border-green-200 text-green-700 bg-green-50',
    description:
      'Plant wedstrijden één voor één — de moeilijkst in te plannen wedstrijden gaan als eerste. ' +
      'Vergelijk het met een trainer die z\'n sterkste spelers als eerste opstelt: het werkt, maar hij kijkt niet of een andere opstelling misschien nog beter uitkomt.',
    when: 'Als je snel wilt zien hoe de speeldag er ongeveer uitziet.',
  },
  {
    value: 'sa',
    label: 'Simulated Annealing',
    badge: 'aanbevolen',
    badgeClass: 'border-blue-200 text-blue-700 bg-blue-50',
    description:
      'Begint met de greedy planning en probeert die daarna te verbeteren door wedstrijden te wisselen en te schuiven. ' +
      'Zoals een trainer die na de eerste opstelling blijft puzzelen — af en toe een wissel terugdraaien om uiteindelijk een betere combinatie te vinden.',
    when: 'De standaardkeuze. Geeft de beste balans tussen kwaliteit en snelheid.',
  },
  {
    value: 'milp',
    label: 'MILP',
    badge: 'traag',
    badgeClass: 'border-orange-200 text-orange-700 bg-orange-50',
    description:
      'Bekijkt alle mogelijke planningen en kiest de beste. Gegarandeerd het beste resultaat — maar bij veel wedstrijden kan dit minuten duren. ' +
      'Zoals een trainer die écht elke mogelijke opstelling op papier uitwerkt voor hij een beslissing neemt.',
    when: 'Als je het absolute maximum wilt en de tijd hebt om te wachten.',
  },
]

onMounted(async () => {
  const data = await getOptimizer()
  algo.value = data.algorithm ?? 'sa'
})

function select(value) {
  algo.value = value
  autosave('optimizer', async () => {
    await saveOptimizer({ algorithm: algo.value })
  })
}
</script>
