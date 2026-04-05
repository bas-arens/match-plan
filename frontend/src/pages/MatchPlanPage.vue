<template>
  <div class="p-8 space-y-6 dark:bg-gray-950 min-h-screen">

    <!-- HEADER -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-brand-dark dark:text-white">Planning</h1>
        <p class="text-sm text-gray-500 mt-0.5">
          {{ planStore.date }}
          <span v-if="planStore.result?.algorithm" class="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-brand-primaryLight text-brand-dark">
            {{ planStore.result.algorithm.toUpperCase() }}
          </span>
        </p>
      </div>

      <div class="flex items-center gap-3">

        <!-- DOWNLOAD BUTTON -->
        <div class="relative" ref="downloadMenuRef">
          <button
            @click="downloadOpen = !downloadOpen"
            class="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-brand-dark border border-gray-200 hover:border-gray-400 rounded px-3 py-1.5 transition-colors"
          >
            <Download :size="14" />
            Download
          </button>

          <!-- DROPDOWN -->
          <div
            v-if="downloadOpen"
            class="absolute right-0 top-full mt-1 w-44 bg-white border border-gray-200 rounded shadow-lg z-50 overflow-hidden"
          >
            <button
              v-for="fmt in formats"
              :key="fmt.id"
              @click="handleDownload(fmt.id)"
              class="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors text-left"
            >
              <span class="text-gray-400 font-mono text-xs w-10">{{ fmt.ext }}</span>
              {{ fmt.label }}
            </button>
          </div>
        </div>

      </div>
    </div>

    <!-- NO RESULT -->
    <div v-if="!scheduled.length" class="flex flex-col items-center justify-center py-24 text-gray-400 space-y-3">
      <CalendarX :size="40" stroke-width="1.5" />
      <p class="text-sm">Geen resultaten. Genereer eerst een planning via de kalender.</p>
    </div>

    <div v-else class="space-y-6" ref="planningRef">

      <!-- GANTT CHART -->
      <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm p-6">
        <GanttChart
          :scheduled="scheduled"
          :preferences="preferences"
          :all-fields="allFields"
          :lockers="lockers"
        />
      </div>

      <!-- LOCKER TABLE -->
      <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center gap-2">
          <DoorOpen :size="18" class="text-gray-400" />
          <h3 class="font-semibold text-brand-dark dark:text-white">Kleedkamers</h3>
        </div>

        <table class="w-full text-sm">
          <thead>
            <!-- SECTION HEADERS -->
            <tr class="text-center text-xs font-bold text-gray-500 uppercase tracking-widest">
              <th colspan="2" class="px-6 pt-4 pb-0">
                <div class="pb-1 border-b-2 border-gray-300">Thuis</div>
              </th>
              <th colspan="2" class="px-6 pt-4 pb-0">
                <div class="pb-1 border-b-2 border-gray-300">Match</div>
              </th>
              <th colspan="2" class="px-6 pt-4 pb-0">
                <div class="pb-1 border-b-2 border-gray-300">Uit</div>
              </th>
            </tr>
            <!-- COLUMN HEADERS -->
            <tr class="bg-gray-50 dark:bg-gray-800 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide">
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
              class="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              <td class="px-6 py-3 font-medium text-gray-800 dark:text-gray-100">{{ m.home }}</td>
              <td class="px-6 py-3 text-gray-500 dark:text-gray-400 tabular-nums">{{ m.home_locker }}</td>
              <td class="px-6 py-3 text-gray-800 tabular-nums border-l border-gray-100">{{ m.time }}</td>
              <td class="px-6 py-3 text-gray-500">{{ m.field_name }}</td>
              <td class="px-6 py-3 font-medium text-gray-800 border-l border-gray-100">{{ m.away }}</td>
              <td class="px-6 py-3 text-gray-500 dark:text-gray-400 tabular-nums">
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
// ─────────────────────────────────────────────────────────────────────────────
// File:    src/pages/MatchPlanPage.vue
// Author:  MatchPlan
// Purpose: Displays the generated match planning result — a Gantt chart for
//          visual scheduling and a locker-room assignment table.
//          Also provides a download button (CSV / Excel / PNG / PDF).
//
// Functions:
//   handleDownload   — delegates to the appropriate download service function
//   onClickOutside   — closes the download dropdown when clicking elsewhere
// ─────────────────────────────────────────────────────────────────────────────
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { planStore } from '@/stores/planStore'
import GanttChart from '@/components/schedule/GanttChart.vue'
import { getPreferences, getFields, getLockers } from '@/services/settings.js'
import { downloadCSV, downloadExcel, downloadPNG, downloadPDF } from '@/services/download.js'
import { CalendarX, DoorOpen, TriangleAlert, Download } from 'lucide-vue-next'

const scheduled    = computed(() => planStore.result?.scheduled ?? [])
const preferences  = ref([])
const allFields    = ref([])
const lockers      = ref([])
const downloadOpen = ref(false)
const downloadMenuRef = ref(null)
const planningRef     = ref(null)

const formats = [
  { id: 'csv',   ext: '.csv',  label: 'CSV'   },
  { id: 'excel', ext: '.xlsx', label: 'Excel' },
  { id: 'png',   ext: '.png',  label: 'PNG'   },
  { id: 'pdf',   ext: '.pdf',  label: 'PDF'   },
]

async function handleDownload(fmt) {
  downloadOpen.value = false
  const date = planStore.date
  const algo = planStore.result?.algorithm ?? ''
  if (fmt === 'csv')   downloadCSV(scheduled.value, date)
  if (fmt === 'excel') downloadExcel(scheduled.value, date)
  if (fmt === 'png')   await downloadPNG(scheduled.value, date, algo)
  if (fmt === 'pdf')   await downloadPDF(scheduled.value, date, algo)
}

function onClickOutside(e) {
  if (downloadMenuRef.value && !downloadMenuRef.value.contains(e.target)) {
    downloadOpen.value = false
  }
}

onMounted(async () => {
  document.addEventListener('click', onClickOutside)
  const [prefs, fields, lks] = await Promise.all([
    getPreferences(),
    getFields(),
    getLockers(),
  ])
  preferences.value = prefs
  allFields.value   = fields
  lockers.value     = lks
})

onUnmounted(() => {
  document.removeEventListener('click', onClickOutside)
})
</script>
