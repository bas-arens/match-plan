<template>
  <main-layout>

    <!-- LEFT SIDE: MATCH LIST -->
    <template #left>
      <MatchList :matches="matches" />
    </template>


    <!-- RIGHT SIDE: CALENDAR + BUTTON + RESULT -->
    <template #right>
      <div class="space-y-4">

        <!-- Calendar -->
        <Calendar v-model="matches" @dateSelected="onDateSelected" />

        <!-- PLAN BUTTON -->
        <button
          class="w-full bg-brand-dark hover:bg-gray-800 text-white font-semibold py-2.5 px-4 rounded-xl transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
          @click="planMatchday"
          :disabled="loading"
        >
          <Loader2 v-if="loading" :size="16" class="animate-spin" />
          <CalendarCheck v-else :size="16" />
          <span>{{ loading ? 'Planner draait...' : 'Plan Matchday' }}</span>
        </button>

        <!-- MATCH COUNT -->
        <MatchCount :count="matches.length" />

        <!-- ERROR MESSAGE -->
        <div v-if="error" class="flex items-center gap-2 text-red-600 text-sm bg-red-50 border border-red-100 rounded-xl px-4 py-3">
          <CircleAlert :size="16" />
          {{ error }}
        </div>

        <!-- EMPTY MESSAGE -->
        <div
          v-if="result && result.status === 'empty'"
          class="text-gray-500 text-sm bg-gray-100 rounded-xl px-4 py-3"
        >
          Geen thuiswedstrijden op deze datum.
        </div>

      </div>
    </template>

  </main-layout>
</template>


<script setup>
import { ref } from "vue"
import { useRouter } from "vue-router"

import MainLayout from "@/components/layout/main-layout.vue"
import Calendar from "@/components/calendar/calendar.vue"
import MatchList from "@/components/matches/match-list.vue"
import MatchCount from "@/components/calendar/match-count.vue"

import { runOptimizer } from "@/services/optimizer.js"
import { planStore } from "@/stores/planStore.js"
import { Loader2, CalendarCheck, CircleAlert } from 'lucide-vue-next'

const router = useRouter()

// MATCHES FROM CALENDAR
const matches = ref([])

// SELECTED DATE
const selectedDate = ref(null)

function onDateSelected(date) {
  selectedDate.value = date
}


// STATUS
const loading = ref(false)
const error = ref(null)
const result = ref(null)


// MAIN FUNCTION
async function planMatchday() {
  if (!selectedDate.value) {
    error.value = "Selecteer eerst een datum."
    return
  }

  loading.value = true
  error.value = null
  result.value = null

  const dateISO = selectedDate.value.toLocaleDateString("sv-SE")

  try {
    const res = await runOptimizer(dateISO)
    result.value = res

    if (res.status === 'ok') {
      planStore.result = res
      planStore.date   = dateISO
      router.push('/matchplan')
    }
  } catch (err) {
    error.value = "Kan planning niet genereren."
  }

  loading.value = false
}
</script>
