<template>
  <div>

    <div v-if="loading" class="text-xs text-gray-400">Laden...</div>

    <div v-else>
      <div class="flex items-center justify-between mb-4">
        <p class="text-sm text-gray-500">
          Zet een team vast op een specifieke tijd, veld en/of kleedkamer. Deze worden altijd gerespecteerd door de optimizer.
        </p>
        <button
          class="text-xs text-gray-400 hover:text-gray-700 transition-colors whitespace-nowrap ml-4"
          @click="addSlot"
        >
          + toevoegen
        </button>
      </div>

      <p v-if="slots.length === 0" class="text-xs text-gray-300 mt-4">Geen vaste slots geconfigureerd.</p>

      <table v-else class="w-full text-sm border-collapse">
        <thead>
          <tr class="text-left text-xs text-gray-400 border-b border-gray-100">
            <th class="pb-2 font-medium">Team</th>
            <th class="pb-2 font-medium">Starttijd</th>
            <th class="pb-2 font-medium">Veld</th>
            <th class="pb-2 font-medium">Kleedkamer</th>
            <th class="pb-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(slot, idx) in slots"
            :key="idx"
            class="border-b border-gray-50 group"
          >
            <!-- Team -->
            <td class="py-2 pr-4">
              <select
                v-model="slot.team"
                @change="debouncedSave"
                class="w-full bg-transparent border-b border-transparent focus:border-gray-300 outline-none text-gray-800 py-0.5 text-sm"
                style="font-family:inherit"
              >
                <option value="" disabled>Kies team...</option>
                <optgroup v-for="(teamList, category) in teams" :key="category" :label="category">
                  <option v-for="name in teamList" :key="name" :value="name">{{ name }}</option>
                </optgroup>
              </select>
            </td>

            <!-- Time -->
            <td class="py-2 pr-4" style="width:100px">
              <input
                type="time"
                v-model="slot.time"
                @input="debouncedSave"
                class="bg-transparent border-b border-transparent focus:border-gray-300 outline-none text-gray-800 py-0.5 text-sm"
                style="font-family:inherit"
              />
            </td>

            <!-- Field -->
            <td class="py-2 pr-4">
              <select
                v-model="slot.field_id"
                @change="debouncedSave"
                class="bg-transparent border-b border-transparent focus:border-gray-300 outline-none text-gray-600 text-sm py-0.5"
                style="font-family:inherit"
              >
                <option :value="null">—</option>
                <option v-for="f in fields" :key="f.id" :value="f.id">{{ f.name }}</option>
              </select>
            </td>

            <!-- Locker -->
            <td class="py-2 pr-4">
              <select
                v-model="slot.locker_id"
                @change="debouncedSave"
                class="bg-transparent border-b border-transparent focus:border-gray-300 outline-none text-gray-600 text-sm py-0.5"
                style="font-family:inherit"
              >
                <option :value="null">—</option>
                <option v-for="l in lockers" :key="l.id" :value="l.id">{{ l.name }}</option>
              </select>
            </td>

            <!-- Delete -->
            <td class="py-2 text-right">
              <button
                @click="removeSlot(idx)"
                class="inline-flex items-center justify-center w-7 h-7 rounded border border-gray-200 text-gray-400 hover:border-red-300 hover:bg-red-50 hover:text-red-500 active:bg-red-100 transition-colors"
              >
                <Trash2 :size="13" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Trash2 } from 'lucide-vue-next'
import { getFixedSlots, saveFixedSlots, getFields, getLockers } from '@/services/settings.js'
import { getTeams } from '@/services/sportlink.js'
import { autosave } from '@/utils/autosave.js'

const slots   = ref([])
const fields  = ref([])
const lockers = ref([])
const teams   = ref({})
const loading = ref(true)

onMounted(async () => {
  const [savedSlots, loadedFields, loadedLockers, loadedTeams] = await Promise.all([
    getFixedSlots(),
    getFields(),
    getLockers(),
    getTeams(),
  ])

  slots.value   = savedSlots.map(s => ({
    team:      s.team ?? '',
    time:      s.time ?? '',
    field_id:  s.field_id ?? null,
    locker_id: s.locker_id ?? null,
  }))
  fields.value  = loadedFields
  lockers.value = loadedLockers
  teams.value   = loadedTeams
  loading.value = false
})

function addSlot() {
  slots.value.push({ team: '', time: '', field_id: null, locker_id: null })
}

function removeSlot(idx) {
  slots.value.splice(idx, 1)
  debouncedSave()
}

function debouncedSave() {
  autosave('fixedslots', async () => {
    const payload = slots.value
      .filter(s => s.team)
      .map(s => ({
        team:      s.team,
        time:      s.time || null,
        field_id:  s.field_id ?? null,
        locker_id: s.locker_id ?? null,
      }))
    await saveFixedSlots(payload)
  })
}
</script>
