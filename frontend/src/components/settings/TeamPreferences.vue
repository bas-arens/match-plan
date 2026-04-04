<template>
  <div>

    <h2 class="text-2xl font-bold mb-4">Teamvoorkeuren</h2>

    <div v-for="(teams, category) in teamPreferences" :key="category" class="mb-8">

      <h3 class="text-xl font-semibold mb-3 text-brand-dark">
        {{ category }}
      </h3>

      <div
        class="grid gap-4"
        style="grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));"
      >
        <div
          v-for="team in teams"
          :key="team.team"
          class="mp-container p-3 space-y-3"
        >
          <!-- Team name -->
          <div class="font-semibold text-brand-dark truncate">{{ team.team }}</div>

          <!-- Time range slider -->
          <div>
            <label class="block text-xs text-gray-600 mb-2">Tijdvenster</label>
            <TimeRangeSlider
              :modelStart="team.rangeStart"
              :modelEnd="team.rangeEnd"
              :min="DAY_START_MIN"
              :max="DAY_END_MIN"
              @update:modelStart="val => { team.rangeStart = val; team.start = minToTime(val) }"
              @update:modelEnd="val => { team.rangeEnd = val; team.end = minToTime(val) }"
              @change="debouncedSave"
            />
          </div>

          <!-- Preferred fields -->
          <div class="text-sm">
            <label class="block text-xs text-gray-600 mb-1">Voorkeursvelden</label>
            <div class="flex flex-col gap-1">
              <label
                v-for="field in fields"
                :key="field.id"
                class="flex items-center gap-2 cursor-pointer"
              >
                <input
                  type="checkbox"
                  :value="field.id"
                  :checked="team.preferred_field_ids.includes(field.id)"
                  @change="toggleField(team, field.id, $event)"
                  class="accent-brand-primary"
                />
                <span>{{ field.name }}</span>
              </label>
            </div>
          </div>

          <!-- Avoid surfaces -->
          <div class="text-sm">
            <label class="block text-xs text-gray-600 mb-1">Vermijd ondergrond</label>
            <div class="flex flex-col gap-1">
              <label
                v-for="surface in availableSurfaces"
                :key="surface.value"
                class="flex items-center gap-2 cursor-pointer"
              >
                <input
                  type="checkbox"
                  :value="surface.value"
                  :checked="team.avoid_surfaces.includes(surface.value)"
                  @change="toggleSurface(team, surface.value, $event)"
                  class="accent-brand-primary"
                />
                <span>{{ surface.label }}</span>
              </label>
            </div>
          </div>

        </div>
      </div>

    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import TimeRangeSlider from "@/components/common/TimeRangeSlider.vue"
import { getTeams } from "@/services/sportlink.js"
import { getPreferences, savePreferences } from "@/services/settings.js"
import { getFields } from "@/services/settings.js"
import { autosave } from "@/utils/autosave.js"

const DAY_START_MIN = 7 * 60   // 07:00
const DAY_END_MIN   = 23 * 60  // 23:00

const teamPreferences = ref({})
const fields = ref([])

const availableSurfaces = [
  { value: "kunstgras", label: "Kunstgras" },
  { value: "natuurgras", label: "Natuurgras" },
]

function timeToMin(t) {
  const [h, m] = t.split(":").map(Number)
  return h * 60 + m
}

function minToTime(min) {
  const h = Math.floor(min / 60).toString().padStart(2, "0")
  const m = (min % 60).toString().padStart(2, "0")
  return `${h}:${m}`
}

function formatMin(val) {
  return minToTime(val)
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
    result[category] = teamList.map((name) => {
      const prev = savedMap[name]
      const start = prev?.start ?? "09:00"
      const end   = prev?.end   ?? "17:00"
      return {
        team:                name,
        category,
        start,
        end,
        rangeStart:          timeToMin(start),
        rangeEnd:            timeToMin(end),
        preferred_field_ids: prev?.preferred_field_ids ?? [],
        avoid_surfaces:      prev?.avoid_surfaces      ?? [],
      }
    })
  }

  teamPreferences.value = result
  await savePreferences(flatten(teamPreferences.value))
})

function flatten(obj) {
  return Object.values(obj).flat().map(({ rangeStart, rangeEnd, ...rest }) => rest)
}

function toggleField(team, fieldId, event) {
  if (event.target.checked) {
    team.preferred_field_ids = [...team.preferred_field_ids, fieldId]
  } else {
    team.preferred_field_ids = team.preferred_field_ids.filter((id) => id !== fieldId)
  }
  debouncedSave()
}

function toggleSurface(team, surface, event) {
  if (event.target.checked) {
    team.avoid_surfaces = [...team.avoid_surfaces, surface]
  } else {
    team.avoid_surfaces = team.avoid_surfaces.filter((s) => s !== surface)
  }
  debouncedSave()
}

function debouncedSave() {
  autosave("teampreferences", async () => {
    await savePreferences(flatten(teamPreferences.value))
  })
}
</script>
