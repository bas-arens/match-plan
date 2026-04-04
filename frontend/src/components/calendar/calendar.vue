<template>
  <div class="p-6 bg-white border border-brand-border shadow-sm rounded-lg w-full">

    <div class="grid grid-cols-2 gap-6">

      <!-- Calendar -->
      <div class="p-4 bg-white rounded flex">
        <v-date-picker 
          transparent
          v-model="selectedDate"
          :rows="1"
          :color="'green'"
          :attributes="attributes"
          :locale="nlLocale"
          class="w-full"
        >
          <!-- Footer: Today button -->
          <template #footer>
            <div class="w-full px-4 pb-3">
              <button
                class="bg-brand-primary hover:bg-brand-primary-dark text-white font-bold w-full px-3 py-1 rounded-md"
                @click="moveToday"
              >
                Vandaag
              </button>
            </div>
          </template>
        </v-date-picker>
      </div>

      <!-- Match Count box wrapper -->
      <div class="p-4 bg-white rounded flex">
        <MatchCount
          v-if="selectedDate"
          :count="matches.length"
          class="w-full h-full"
        />
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import MatchCount from '@/components/calendar/match-count.vue'

import {
  getDatumLijst,
  getProgrammaOpDatum
} from '@/services/sportlink.js'

/* ---------------------------
   Props + Emits
--------------------------- */
const props = defineProps({
  modelValue: Array
})
const emit = defineEmits(['update:modelValue'])

/* ---------------------------
   State
--------------------------- */
const selectedDate = ref(null)
const matches = ref(props.modelValue)
const availableDates = ref([])

const calendar = ref(null)
const selectedColor = ref('green');

/* ---------------------------
   NL locale
--------------------------- */
const nlLocale = {
  id: 'nl',
  firstDayOfWeek: 2,
  monthNames: [
    'januari', 'februari', 'maart', 'april', 'mei', 'juni',
    'juli', 'augustus', 'september', 'oktober', 'november', 'december'
  ],
  weekdays: ['ma', 'di', 'wo', 'do', 'vr', 'za', 'zo']
}

/* ---------------------------
   Highlight matchdays
--------------------------- */
const attributes = computed(() => [
  {
    key: 'matchdays',
    dot: 'brand-primary',
    dates: availableDates.value,
  },
  {
    key: 'selected',
    highlight: { color: selectedColor.value },
    dates: selectedDate.value
  }
])





/* ---------------------------
   Helpers
--------------------------- */
// function toISO(d) {
//   return d.toISOString().split('T')[0]
// }

function toISO(d) {
  return d.toLocaleDateString("sv-SE"); // → YYYY-MM-DD without timezone shift
}


/* ---------------------------
   Load match days & today
--------------------------- */
onMounted(async () => {
  const raw = await getDatumLijst()

  // Convert ISO strings into real Date objects
  availableDates.value = raw.map((d) => new Date(d))

  const today = new Date()
  selectedDate.value = today

  await loadMatches(toISO(today))
})


/* ---------------------------
   Fetch matches
--------------------------- */
async function loadMatches(dateStr) {
  const newMatches = await getProgrammaOpDatum(dateStr)
  matches.value = newMatches
  emit('update:modelValue', newMatches)
}

/* ---------------------------
   Watch date selection
--------------------------- */
watch(selectedDate, async (newDate) => {
  if (!newDate) return


  emit("dateSelected", newDate)

  await loadMatches(toISO(newDate))
})


/* ---------------------------
   Footer button: Today
--------------------------- */
function moveToday() {
  const today = new Date()
  selectedDate.value = today
  calendar.value.move(today)
}


</script>

<style>

/* SELECTED DAY — force visible */
.vc-day.is-selected .vc-day-content,
.vc-day.is-selected .vc-day-content *,
.vc-day.is-selected .vc-highlight-content,
.vc-day.is-selected .vc-highlight-content *,
.vc-day.is-selected .vc-date {
  color: var(--brand-primary) !important;
}

/* SELECTED DAY background override (remove white/blue fill) */
.vc-day.is-selected .vc-day-content,
.vc-day.is-selected .vc-day-content.is-highlight,
.vc-day.is-selected .vc-day-content.is-start,
.vc-day.is-selected .vc-day-content.is-end,
.vc-day.is-selected .vc-highlight-bg {
  background: transparent !important;
  border: 2px solid var(--brand-primary) !important;
  box-shadow: none !important;
}

/* DOT color */
.vc-dot {
  background-color: var(--brand-primary) !important;
}

/* HOVER (works even for selected days) */
.vc-day:not(.is-disabled):hover .vc-day-content {
  background-color: var(--brand-primary-light) !important;
  color: var(--brand-primary) !important;
}



</style>

