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
          class="w-full bg-brand-dark hover:bg-gray-800 text-white font-semibold py-2.5 px-4 rounded-xl transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
          @click="planMatchday"
          :disabled="loading"
        >
          <Loader2 v-if="loading" :size="16" class="animate-spin" />
          <CalendarCheck v-else :size="16" />
          <span>{{ loading ? 'Planner draait...' : 'Plan Matchday' }}</span>
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

function onDateSelected(date) {
  selectedDate.value = date
}

async function planMatchday() {
  if (!selectedDate.value) {
    notify('Selecteer eerst een datum.')
    return
  }

  loading.value = true
  const dateISO = selectedDate.value.toLocaleDateString('sv-SE')

  try {
    const res = await runOptimizer(dateISO)
    if (res.status === 'ok') {
      planStore.result = res
      planStore.date   = dateISO
      router.push('/matchplan')
    } else {
      notify('Geen thuiswedstrijden op deze datum.')
    }
  } catch {
    notify('Kan planning niet genereren. Controleer de verbinding.')
  } finally {
    loading.value = false
  }
}
</script>
