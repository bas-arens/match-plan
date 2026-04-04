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
      'Plaatst wedstrijden één voor één op basis van moeilijkheidsgraad — smalste tijdvenster eerst. ' +
      'Voor elke wedstrijd kiest het de best beschikbare combinatie van veld en tijdstip. ' +
      'Deterministisch: geeft altijd dezelfde uitkomst.',
    when: 'Snel een eerste planning zien, of als de speeldag eenvoudig is.',
  },
  {
    value: 'sa',
    label: 'Simulated Annealing',
    badge: 'aanbevolen',
    badgeClass: 'border-blue-200 text-blue-700 bg-blue-50',
    description:
      'Start vanuit de greedy oplossing en verbetert die iteratief via willekeurige aanpassingen. ' +
      'Accepteert soms tijdelijk slechtere oplossingen om lokale optima te vermijden — vergelijkbaar met afkoelend metaal. ' +
      'Levert significant betere resultaten dan greedy met een acceptabele rekentijd.',
    when: 'Standaardkeuze voor de meeste speeldagen.',
  },
  {
    value: 'milp',
    label: 'MILP',
    badge: 'traag',
    badgeClass: 'border-orange-200 text-orange-700 bg-orange-50',
    description:
      'Mixed Integer Linear Programming: formuleert de planning als een wiskundig optimalisatieprobleem ' +
      'en lost dat exact op. Gegarandeerd de beste mogelijke oplossing, maar de rekentijd groeit snel ' +
      'bij meer wedstrijden of velden.',
    when: 'Kleine speeldagen, of als de kwaliteit van de planning cruciaal is en tijd geen rol speelt.',
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
