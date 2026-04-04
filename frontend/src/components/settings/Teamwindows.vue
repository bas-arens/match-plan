<template>
  <div>

    <!-- Title -->
    <h2 class="text-2xl font-bold mb-4">Team tijdsvensters</h2>

    <!-- Category blocks -->
    <div v-for="(teams, category) in teamWindows" :key="category" class="mb-8">

      <!-- Category Title -->
      <h3 class="text-xl font-semibold mb-3 text-brand-dark">
        {{ category }}
      </h3>

      <!-- Responsive grid for teams -->
      <div
        class="grid gap-4"
        style="grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));"
      >
        <div
          v-for="team in teams"
          :key="team.team"
          class="mp-container p-3 space-y-2"
        >
          <!-- Team name -->
          <div class="font-semibold text-brand-dark truncate">
            {{ team.team }}
          </div>

          <!-- Time pickers -->
          <div class="grid grid-cols-2 gap-2 text-sm">
            <div>
              <label class="block text-xs text-gray-600 mb-1">Vanaf</label>
              <TimeSelect
                v-model="team.start"
                @change="debouncedSave"
              />
            </div>

            <div>
              <label class="block text-xs text-gray-600 mb-1">Tot</label>
              <TimeSelect
                v-model="team.end"
                @change="debouncedSave"
              />
            </div>
          </div>
        </div>
      </div>

    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { getTeams } from "@/services/sportlink.js"
import { getWindows, saveWindows } from "@/services/settings.js"
import { autosave } from "@/utils/autosave.js"
import TimeSelect from "@/components/common/time-select.vue"


const teamWindows = ref({})

onMounted(async () => {
  // 1️⃣ Load Sportlink categories
  const categories = await getTeams()   


  // 2️⃣ Load saved windows
  const saved = await getWindows()
  // saved = [{ team: "De Esch 1", category: "...", start:"", end:"" }]

  const savedMap = {}
  for (const w of saved) savedMap[w.team] = w

  // 3️⃣ Merge Sportlink teams with saved settings
  const result = {}

  for (const [category, teamList] of Object.entries(categories)) {
    result[category] = teamList.map((name) => {
      const prev = savedMap[name]

      return {
        team: name,
        category,
        start: prev ? prev.start : "09:00",
        end:   prev ? prev.end : "17:00",
      }
    })
  }

  teamWindows.value = result

  // 4️⃣ Save merged version so backend stays in sync
  await saveWindows(flatten(teamWindows.value))
})

/* Helper to flatten {category → teams[]} into a single list */
function flatten(obj) {
  return Object.values(obj).flat()
}

/* Autosave debounce wrapper */
function debouncedSave() {
  autosave("teamwindows", async () => {
    await saveWindows(flatten(teamWindows.value))
  })
}
</script>
