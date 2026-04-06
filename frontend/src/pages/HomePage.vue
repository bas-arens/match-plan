<template>
  <main-layout>

    <!-- LEFT SIDE: MATCH LIST -->
    <template #left>
      <MatchList :matches="matches" />
    </template>

    <!-- RIGHT SIDE: CALENDAR + BUTTON + COUNT -->
    <template #right>
      <div class="space-y-4">

        <Calendar v-model="matches" @dateSelected="onDateSelected" />

        <button
          class="w-full relative overflow-hidden bg-brand-dark hover:bg-gray-800 text-white font-semibold py-2.5 px-4 rounded-xl transition-colors flex items-center justify-center gap-2 disabled:cursor-wait"
          @click="planMatchday"
          :disabled="loading"
        >
          <!-- Progress bar fill -->
          <div
            v-if="loading"
            class="absolute inset-0 bg-white/15 origin-left"
            :style="{ transform: `scaleX(${progress})` }"
          />
          <span class="relative flex items-center gap-2">
            <Loader2 v-if="loading" :size="16" class="animate-spin" />
            <CalendarCheck v-else :size="16" />
            {{ loading ? 'Planner draait...' : 'Plan Matchday' }}
          </span>
        </button>

        <MatchCount :count="matches.length" />

      </div>
    </template>

  </main-layout>
</template>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// File:    src/pages/HomePage.vue
// Author:  Bas Arens
// Purpose: Main landing page — shows the calendar and match list side-by-side.
//          Lets the user pick a date and trigger the planning optimizer.
//
// Functions:
//   onDateSelected  — stores the Date object emitted by the Calendar component
//   planMatchday    — calls the optimizer API for the selected date; on success
//                     saves the result to planStore and navigates to /matchplan
// ─────────────────────────────────────────────────────────────────────────────
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import MainLayout  from '@/components/layout/main-layout.vue'
import Calendar    from '@/components/calendar/calendar.vue'
import MatchList   from '@/components/matches/match-list.vue'
import MatchCount  from '@/components/calendar/match-count.vue'
import { runOptimizer } from '@/services/optimizer.js'
import { planStore }    from '@/stores/planStore.js'
import { useNotification } from '@/composables/useNotification.js'
import { Loader2, CalendarCheck } from 'lucide-vue-next'

const router       = useRouter()
const { notify }   = useNotification()
const matches      = ref([])
const selectedDate = ref(null)
const loading      = ref(false)
const progress     = ref(0)
let progressRAF    = null

function startProgress() {
  const start = performance.now()
  progress.value = 0

  function tick() {
    const elapsed = (performance.now() - start) / 1000  // seconds
    // Logarithmic ease: jumps to ~50% in first second, then crawls toward 90%
    progress.value = Math.min(0.92, 1 - 1 / (1 + elapsed * 1.5))
    progressRAF = requestAnimationFrame(tick)
  }
  progressRAF = requestAnimationFrame(tick)
}

function stopProgress() {
  if (progressRAF) cancelAnimationFrame(progressRAF)
  progress.value = 1
}

function onDateSelected(date) {
  selectedDate.value = date
}

async function planMatchday() {
  if (!selectedDate.value) {
    notify('Selecteer eerst een datum.')
    return
  }

  loading.value = true
  startProgress()
  const dateISO = selectedDate.value.toLocaleDateString('sv-SE')

  try {
    const res = await runOptimizer(dateISO)
    stopProgress()
    if (res.status === 'ok') {
      planStore.result = res
      planStore.date   = dateISO
      // Brief pause so user sees the bar hit 100%
      await new Promise(r => setTimeout(r, 250))
      router.push('/matchplan')
    } else {
      notify('Geen thuiswedstrijden op deze datum.')
    }
  } catch {
    stopProgress()
    notify('Kan planning niet genereren. Controleer de verbinding.')
  } finally {
    loading.value = false
    progress.value = 0
  }
}
</script>
