<template>
  <div>

    <div v-if="loading" class="text-xs text-gray-400">Laden...</div>

    <div v-else>
      <table class="w-full text-sm border-collapse">
        <thead>
          <tr class="text-left text-xs text-gray-400 border-b border-gray-200">
            <th class="pb-2 pr-6 font-medium w-48">Team</th>
            <th class="pb-2 pr-3 font-medium">Vanaf</th>
            <th class="pb-2 pr-6 font-medium">Tot</th>
            <th
              v-for="field in fields"
              :key="field.id"
              class="pb-2 pr-4 font-medium text-center"
            >{{ field.name }}</th>
            <th class="pb-2 pr-4 font-medium text-center text-xs">Kunstgras<br>vermijden</th>
            <th class="pb-2 font-medium text-center text-xs">Natuurgras<br>vermijden</th>
          </tr>
        </thead>

        <tbody>
          <template v-for="(teams, category) in teamPreferences" :key="category">

            <!-- CATEGORY ROW -->
            <tr>
              <td
                :colspan="3 + fields.length + 2"
                class="pt-6 pb-1 text-xs font-bold uppercase tracking-widest text-gray-400"
              >{{ category }}</td>
            </tr>

            <!-- TEAM ROWS -->
            <tr
              v-for="team in teams"
              :key="team.team"
              class="border-b border-gray-50 hover:bg-gray-50 transition-colors"
            >
              <!-- Team name -->
              <td class="py-2 pr-6 text-gray-700 truncate max-w-[180px]">
                {{ team.team }}
              </td>

              <!-- Vanaf -->
              <td class="py-2 pr-3">
                <select
                  v-model="team.start"
                  @change="debouncedSave"
                  class="bg-transparent border-b border-gray-200 focus:border-gray-500 outline-none text-xs text-gray-700 py-0.5 pr-1"
                >
                  <option v-for="t in times" :key="t" :value="t">{{ t }}</option>
                </select>
              </td>

              <!-- Tot -->
              <td class="py-2 pr-6">
                <select
                  v-model="team.end"
                  @change="debouncedSave"
                  class="bg-transparent border-b border-gray-200 focus:border-gray-500 outline-none text-xs text-gray-700 py-0.5 pr-1"
                >
                  <option v-for="t in times" :key="t" :value="t">{{ t }}</option>
                </select>
              </td>

              <!-- Field preference checkboxes -->
              <td
                v-for="field in fields"
                :key="field.id"
                class="py-2 pr-4 text-center"
              >
                <input
                  type="checkbox"
                  :checked="team.preferred_field_ids.includes(field.id)"
                  @change="toggleField(team, field.id, $event)"
                  class="accent-gray-700 cursor-pointer"
                />
              </td>

              <!-- Avoid kunstgras -->
              <td class="py-2 pr-4 text-center">
                <input
                  type="checkbox"
                  :checked="team.avoid_surfaces.includes('kunstgras')"
                  @change="toggleSurface(team, 'kunstgras', $event)"
                  class="accent-gray-700 cursor-pointer"
                />
              </td>

              <!-- Avoid natuurgras -->
              <td class="py-2 text-center">
                <input
                  type="checkbox"
                  :checked="team.avoid_surfaces.includes('natuurgras')"
                  @change="toggleSurface(team, 'natuurgras', $event)"
                  class="accent-gray-700 cursor-pointer"
                />
              </td>
            </tr>

          </template>
        </tbody>
      </table>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getTeams } from '@/services/sportlink.js'
import { getPreferences, savePreferences, getFields } from '@/services/settings.js'
import { autosave } from '@/utils/autosave.js'

const teamPreferences = ref({})
const fields          = ref([])
const loading         = ref(true)

// Time options: 15-min intervals from 06:00 to 23:00
const times = []
for (let h = 6; h <= 23; h++) {
  for (const m of ['00', '15', '30', '45']) {
    times.push(`${String(h).padStart(2, '0')}:${m}`)
  }
}

onMounted(async () => {
  const [categories, saved, loadedFields] = await Promise.all([
    getTeams(),
    getPreferences(),
    getFields(),
  ])

  fields.value = loadedFields

  const savedMap = {}
  for (const p of saved) savedMap[p.team] = p

  const result = {}
  for (const [category, teamList] of Object.entries(categories)) {
    result[category] = teamList.map(name => {
      const prev = savedMap[name]
      return {
        team:                name,
        category,
        start:               prev?.start               ?? '09:00',
        end:                 prev?.end                 ?? '17:00',
        preferred_field_ids: prev?.preferred_field_ids ?? [],
        avoid_surfaces:      prev?.avoid_surfaces      ?? [],
      }
    })
  }

  teamPreferences.value = result
  await savePreferences(flatten(teamPreferences.value))
  loading.value = false
})

function flatten(obj) {
  return Object.values(obj).flat()
}

function toggleField(team, fieldId, event) {
  if (event.target.checked) {
    team.preferred_field_ids = [...team.preferred_field_ids, fieldId]
  } else {
    team.preferred_field_ids = team.preferred_field_ids.filter(id => id !== fieldId)
  }
  debouncedSave()
}

function toggleSurface(team, surface, event) {
  if (event.target.checked) {
    team.avoid_surfaces = [...team.avoid_surfaces, surface]
  } else {
    team.avoid_surfaces = team.avoid_surfaces.filter(s => s !== surface)
  }
  debouncedSave()
}

function debouncedSave() {
  autosave('teampreferences', async () => {
    await savePreferences(flatten(teamPreferences.value))
  })
}
</script>
