<template>
  <div class="p-8 space-y-6">

    <!-- HEADER -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-brand-dark">Planning</h1>
        <p class="text-sm text-gray-500 mt-0.5">
          {{ planStore.date }}
          <span v-if="planStore.result?.algorithm" class="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-brand-primaryLight text-brand-dark">
            {{ planStore.result.algorithm.toUpperCase() }}
          </span>
        </p>
      </div>
      <router-link
        to="/calendar"
        class="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-brand-dark transition-colors"
      >
        <ArrowLeft :size="16" />
        Terug naar kalender
      </router-link>
    </div>

    <!-- NO RESULT -->
    <div v-if="!scheduled.length" class="flex flex-col items-center justify-center py-24 text-gray-400 space-y-3">
      <CalendarX :size="40" stroke-width="1.5" />
      <p class="text-sm">Geen resultaten. Genereer eerst een planning via de kalender.</p>
    </div>

    <div v-else class="space-y-6">

      <!-- GANTT CHART -->
      <div class="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
        <GanttChart
          :scheduled="scheduled"
          :preferences="preferences"
          :all-fields="allFields"
          :lockers="lockers"
        />
      </div>

      <!-- LOCKER TABLE -->
      <div class="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center gap-2">
          <DoorOpen :size="18" class="text-gray-400" />
          <h3 class="font-semibold text-brand-dark">Kleedkamers</h3>
        </div>

        <table class="w-full text-sm">
          <thead>
            <!-- SECTION HEADERS -->
            <tr class="text-left text-xs font-bold text-gray-400 uppercase tracking-widest border-b border-gray-100">
              <th colspan="2" class="px-6 pt-4 pb-1">Thuis</th>
              <th colspan="2" class="px-6 pt-4 pb-1 border-l border-gray-100">Match</th>
              <th colspan="2" class="px-6 pt-4 pb-1 border-l border-gray-100">Uit</th>
            </tr>
            <!-- COLUMN HEADERS -->
            <tr class="bg-gray-50 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide">
              <th class="px-6 py-2">Team</th>
              <th class="px-6 py-2">Kleedkamer</th>
              <th class="px-6 py-2 border-l border-gray-100">Tijd</th>
              <th class="px-6 py-2">Veld</th>
              <th class="px-6 py-2 border-l border-gray-100">Team</th>
              <th class="px-6 py-2">Kleedkamer</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="m in scheduled"
              :key="m.match_id"
              class="hover:bg-gray-50 transition-colors"
            >
              <td class="px-6 py-3 font-medium text-gray-800">{{ m.home }}</td>
              <td class="px-6 py-3 text-gray-500 tabular-nums">{{ m.home_locker }}</td>
              <td class="px-6 py-3 text-gray-800 tabular-nums border-l border-gray-100">{{ m.time }}</td>
              <td class="px-6 py-3 text-gray-500">{{ m.field_name }}</td>
              <td class="px-6 py-3 font-medium text-gray-800 border-l border-gray-100">{{ m.away }}</td>
              <td class="px-6 py-3 text-gray-500 tabular-nums">
                {{ m.away_locker }}
                <span v-if="m.penalty > 0" class="ml-2 inline-flex items-center gap-1 text-orange-500 text-xs font-medium">
                  <TriangleAlert :size="12" />
                  gedeeld
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
  </div>
</template>


<script setup>
import { computed, ref, onMounted } from 'vue'
import { planStore } from '@/stores/planStore'
import GanttChart from '@/components/schedule/GanttChart.vue'
import { getPreferences, getFields, getLockers } from '@/services/settings.js'
import { ArrowLeft, CalendarX, DoorOpen, TriangleAlert } from 'lucide-vue-next'

const scheduled    = computed(() => planStore.result?.scheduled ?? [])
const preferences  = ref([])
const allFields    = ref([])
const lockers      = ref([])

onMounted(async () => {
  const [prefs, fields, lks] = await Promise.all([
    getPreferences(),
    getFields(),
    getLockers(),
  ])
  preferences.value = prefs
  allFields.value   = fields
  lockers.value     = lks
})
</script>
