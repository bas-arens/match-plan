<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-bold uppercase tracking-widest text-gray-400">Velden</h2>
      <button class="text-xs text-gray-400 hover:text-gray-700 transition-colors" @click="addField">
        + toevoegen
      </button>
    </div>

    <table class="w-full text-sm">
      <thead>
        <tr class="text-left text-xs text-gray-400 border-b border-gray-100">
          <th class="pb-2 font-medium">Naam</th>
          <th class="pb-2 font-medium">Grastype</th>
          <th class="pb-2"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="field in fields" :key="field.id" class="border-b border-gray-50 group">
          <td class="py-2 pr-4">
            <input
              v-model="field.name"
              @input="saveWithDebounce"
              class="w-full bg-transparent border-b border-transparent focus:border-gray-300 outline-none text-gray-800 py-0.5"
            />
          </td>
          <td class="py-2 pr-4">
            <select
              v-model="field.surface"
              @change="saveWithDebounce"
              class="bg-transparent border-b border-transparent focus:border-gray-300 outline-none text-gray-600 text-xs py-0.5"
            >
              <option value="kunstgras">Kunstgras</option>
              <option value="natuurgras">Natuurgras</option>
            </select>
          </td>
          <td class="py-2 text-right">
            <button
              @click="removeField(field.id)"
              class="inline-flex items-center justify-center w-7 h-7 rounded border border-gray-200 text-gray-400 hover:border-red-300 hover:bg-red-50 hover:text-red-500 active:bg-red-100 transition-colors"
            >
              <Trash2 :size="13" />
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <p v-if="fields.length === 0" class="text-xs text-gray-300 mt-4">Geen velden geconfigureerd.</p>
  </div>
</template>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// File:    src/components/settings/Fields.vue
// Author:  Bas Arens
// Purpose: Settings panel for managing football fields — name, grass type.
//          Changes are auto-saved via a debounced save (600 ms).
//          New field IDs are generated with crypto.randomUUID().
//
// Functions:
//   addField        — appends a new default field and triggers a save
//   removeField     — removes a field by id and triggers a save
//   saveWithDebounce — debounced call to saveFields via autosave
// ─────────────────────────────────────────────────────────────────────────────
import { ref, onMounted } from 'vue'
import { Trash2 } from 'lucide-vue-next'
import { getFields, saveFields } from '@/services/settings'
import { autosave } from '@/utils/autosave'

const fields = ref([])

onMounted(async () => {
  fields.value = await getFields()
})

function addField() {
  fields.value.push({ id: crypto.randomUUID(), name: `Veld ${fields.value.length + 1}`, type: 'full', surface: 'kunstgras' })
  saveWithDebounce()
}

function removeField(id) {
  fields.value = fields.value.filter(f => f.id !== id)
  saveWithDebounce()
}

function saveWithDebounce() {
  autosave('fields', async () => { await saveFields(fields.value) })
}
</script>
