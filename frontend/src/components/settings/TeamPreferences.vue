<template>
  <div>

    <div v-if="loading" class="text-xs text-gray-400">Laden...</div>

    <div v-else>
      <table class="w-full text-sm border-collapse">
        <thead>
          <!-- SECTION HEADERS -->
          <tr class="text-center text-xs font-bold text-gray-500 uppercase tracking-widest">
            <th class="pt-4 pb-0 pr-4 text-left" style="width:160px">
              <div class="pb-1 border-b-2 border-gray-300 text-left">Team</div>
            </th>
            <th class="pt-4 pb-0 pr-6" style="width:170px">
              <div class="pb-1 border-b-2 border-gray-300">Tijdvenster</div>
            </th>
            <th :colspan="fields.length" class="pt-4 pb-0 pr-2">
              <div class="pb-1 border-b-2 border-gray-300">Voorkeursvelden</div>
            </th>
            <th :colspan="lockers.length" class="pt-4 pb-0 pr-2">
              <div class="pb-1 border-b-2 border-gray-300">Kleedkamers</div>
            </th>
            <th colspan="2" class="pt-4 pb-0">
              <div class="pb-1 border-b-2 border-gray-300">Vermijd ondergrond</div>
            </th>
          </tr>
          <!-- COLUMN HEADERS -->
          <tr class="text-xs text-gray-400 border-b border-gray-200">
            <th class="py-2 pr-4 font-medium text-left"></th>
            <th class="py-2 pr-6 font-medium"></th>
            <th
              v-for="field in fields"
              :key="'fh-' + field.id"
              class="py-2 pr-2 font-medium text-center"
              style="width:48px"
            >{{ field.name }}</th>
            <th
              v-for="locker in lockers"
              :key="'lh-' + locker.id"
              class="py-2 pr-2 font-medium text-center"
              style="width:48px"
            >{{ locker.name }}</th>
            <th class="py-2 pr-2 font-medium text-center" style="width:56px">Kunstgras</th>
            <th class="py-2 font-medium text-center" style="width:56px">Natuurgras</th>
          </tr>
        </thead>

        <tbody>
          <template v-for="(teams, category) in teamPreferences" :key="category">

            <!-- CATEGORY ROW -->
            <tr>
              <td
                :colspan="2 + fields.length + lockers.length + 2"
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
              <td class="py-3 pr-4 text-gray-700 truncate" style="max-width:160px">
                {{ team.team }}
              </td>

              <!-- Time range slider -->
              <td class="py-3 pr-6" style="width:170px">
                <TimeRangeSlider
                  :modelStart="team.rangeStart"
                  :modelEnd="team.rangeEnd"
                  :min="DAY_START_MIN"
                  :max="DAY_END_MIN"
                  @update:modelStart="val => { team.rangeStart = val; team.start = minToTime(val); debouncedSave() }"
                  @update:modelEnd="val => { team.rangeEnd = val; team.end = minToTime(val); debouncedSave() }"
                />
              </td>

              <!-- Field preference checkboxes -->
              <td
                v-for="field in fields"
                :key="'f-' + field.id"
                class="py-3 pr-2 text-center"
              >
                <input
                  type="checkbox"
                  :checked="team.preferred_field_ids.includes(field.id)"
                  @change="toggleItem(team, 'preferred_field_ids', field.id, $event)"
                  class="accent-gray-700 cursor-pointer"
                />
              </td>

              <!-- Locker preference checkboxes -->
              <td
                v-for="locker in lockers"
                :key="'l-' + locker.id"
                class="py-3 pr-2 text-center"
              >
                <input
                  type="checkbox"
                  :checked="team.preferred_locker_ids.includes(locker.id)"
                  @change="toggleItem(team, 'preferred_locker_ids', locker.id, $event)"
                  class="accent-gray-700 cursor-pointer"
                />
              </td>

              <!-- Avoid kunstgras -->
              <td class="py-3 pr-4 text-center">
                <input
                  type="checkbox"
                  :checked="team.avoid_surfaces.includes('kunstgras')"
                  @change="toggleSurface(team, 'kunstgras', $event)"
                  class="accent-gray-700 cursor-pointer"
                />
              </td>

              <!-- Avoid natuurgras -->
              <td class="py-3 text-center">
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
// ─────────────────────────────────────────────────────────────────────────────
// File:    src/components/settings/TeamPreferences.vue
// Author:  Bas Arens
// Purpose: Settings table for per-team planning preferences — time windows
//          (via drag slider), preferred fields, preferred locker rooms, and
//          surfaces to avoid. Teams are grouped by Sportlink category.
//          All changes are auto-saved via a debounced save (600 ms).
//
// Functions:
//   flatten         — converts { category → teams[] } to a flat preferences array
//   toggleItem      — adds/removes a field or locker id from a team's preference list
//   toggleSurface   — adds/removes a surface string from a team's avoid list
//   debouncedSave   — debounced call to savePreferences via autosave
// ─────────────────────────────────────────────────────────────────────────────
import { ref, onMounted } from 'vue'
import TimeRangeSlider from '@/components/common/TimeRangeSlider.vue'
import { getTeams } from '@/services/sportlink.js'
import { getPreferences, savePreferences, getFields, getLockers } from '@/services/settings.js'
import { autosave } from '@/utils/autosave.js'
import { timeToMin, minToTime } from '@/utils/time.js'

const DAY_START_MIN = 7 * 60
const DAY_END_MIN   = 21 * 60

const teamPreferences = ref({})
const fields          = ref([])
const lockers         = ref([])
const loading         = ref(true)

onMounted(async () => {
  const [categories, saved, loadedFields, loadedLockers] = await Promise.all([
    getTeams(),
    getPreferences(),
    getFields(),
    getLockers(),
  ])

  fields.value  = loadedFields
  lockers.value = loadedLockers

  const savedMap = {}
  for (const p of saved) savedMap[p.team] = p

  const result = {}
  for (const [category, teamList] of Object.entries(categories)) {
    result[category] = teamList.map(name => {
      const prev  = savedMap[name]
      const start = prev?.start ?? '09:00'
      const end   = prev?.end   ?? '17:00'
      return {
        team:                name,
        category,
        start,
        end,
        rangeStart:          timeToMin(start),
        rangeEnd:            timeToMin(end),
        preferred_field_ids:  prev?.preferred_field_ids  ?? [],
        preferred_locker_ids: prev?.preferred_locker_ids ?? [],
        avoid_surfaces:       prev?.avoid_surfaces       ?? [],
      }
    })
  }

  teamPreferences.value = result
  await savePreferences(flatten(teamPreferences.value))
  loading.value = false
})

function flatten(obj) {
  return Object.values(obj).flat().map(({ rangeStart, rangeEnd, ...rest }) => rest)
}

function toggleItem(team, key, id, event) {
  if (event.target.checked) {
    team[key] = [...team[key], id]
  } else {
    team[key] = team[key].filter(x => x !== id)
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
