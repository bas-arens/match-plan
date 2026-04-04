<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-2xl font-bold">Velden</h2>

      <button
        class="px-3 py-1 bg-brand-primary hover:bg-brand-primary-dark text-white rounded-md text-sm"
        @click="addField"
      >
        + Veld toevoegen
      </button>
    </div>

    <div
      class="grid gap-3"
      style="grid-template-columns: repeat(auto-fit, minmax(220px, 260px));"
    >
      <div
        v-for="field in fields"
        :key="field.id"
        class="mp-container flex flex-col gap-3"
      >
        <!-- Field name -->
        <div>
          <label class="block text-sm text-gray-600 mb-1">Naam</label>
          <input
            v-model="field.name"
            @input="saveWithDebounce"
            class="w-full border border-brand-border rounded px-2 py-1 text-sm"
          />
        </div>

        <!-- Field type -->
        <div>
          <label class="block text-sm text-gray-600 mb-1">Type veld</label>
          <select
            v-model="field.type"
            @change="saveWithDebounce"
            class="w-full border border-brand-border rounded px-2 py-1 text-sm"
          >
            <option value="full">Heel veld</option>
            <option value="half">Half veld</option>
            <option value="quarter">Kwart veld</option>
          </select>
        </div>

        <!-- Surface -->
        <div>
          <label class="block text-sm text-gray-600 mb-1">Grastype</label>
          <select
            v-model="field.surface"
            @change="saveWithDebounce"
            class="w-full border border-brand-border rounded px-2 py-1 text-sm"
          >
            <option value="kunstgras">Kunstgras</option>
            <option value="natuurgras">Natuurgras</option>
          </select>
        </div>

        <!-- Delete -->
        <div
          class="mt-2 px-2 py-1 rounded-md text-center cursor-pointer
                 bg-red-50 text-red-600 text-sm hover:bg-red-100"
          @click="removeField(field.id)"
        >
          Verwijder veld
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { getFields, saveFields } from "@/services/settings";
import { autosave } from "@/utils/autosave";

const fields = ref([]);

onMounted(async () => {
  fields.value = await getFields();
});

function addField() {
  const newId = Date.now();
  fields.value.push({
    id: newId,
    name: `Veld ${fields.value.length + 1}`,
    type: "full",
    surface: "kunstgras"
  });
  saveWithDebounce();
}

function removeField(id) {
  fields.value = fields.value.filter((f) => f.id !== id);
  saveWithDebounce();
}

function saveWithDebounce() {
  autosave("fields", async () => {
    await saveFields(fields.value);
  });
}
</script>
