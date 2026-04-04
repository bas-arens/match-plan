<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-bold uppercase tracking-widest text-gray-400">Kleedkamers</h2>
      <button class="text-xs text-gray-400 hover:text-gray-700 transition-colors" @click="addRoom">
        + toevoegen
      </button>
    </div>

    <table class="w-full text-sm">
      <thead>
        <tr class="text-left text-xs text-gray-400 border-b border-gray-100">
          <th class="pb-2 font-medium">Naam</th>
          <th class="pb-2"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="room in rooms" :key="room.id" class="border-b border-gray-50">
          <td class="py-2 pr-4">
            <input
              v-model="room.name"
              @input="saveWithDebounce"
              class="w-full bg-transparent border-b border-transparent focus:border-gray-300 outline-none text-gray-800 py-0.5"
              placeholder="Naam"
            />
          </td>
          <td class="py-2 text-right">
            <button
              @click="removeRoom(room.id)"
              class="inline-flex items-center justify-center w-7 h-7 rounded border border-gray-200 text-gray-400 hover:border-red-300 hover:bg-red-50 hover:text-red-500 active:bg-red-100 transition-colors"
            >
              <Trash2 :size="13" />
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <p v-if="rooms.length === 0" class="text-xs text-gray-300 mt-4">Geen kleedkamers geconfigureerd.</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Trash2 } from 'lucide-vue-next'
import { getLockers, saveLockers } from '@/services/settings'
import { autosave } from '@/utils/autosave'

const rooms = ref([])

onMounted(async () => {
  rooms.value = await getLockers()
})

function addRoom() {
  rooms.value.push({ id: Date.now(), name: `${rooms.value.length + 1}` })
  saveWithDebounce()
}

function removeRoom(id) {
  rooms.value = rooms.value.filter(r => r.id !== id)
  saveWithDebounce()
}

function saveWithDebounce() {
  autosave('lockers', async () => { await saveLockers(rooms.value) })
}
</script>
