<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-2xl font-bold">Kleedkamers</h2>

      <button
        class="px-3 py-1 bg-brand-primary hover:bg-brand-primary-dark text-white rounded-md text-sm"
        @click="addRoom"
      >
        + Toevoegen
      </button>
    </div>

    <div
      class="grid gap-3"
      style="grid-template-columns: repeat(auto-fit, minmax(140px, 160px));"
    >
      <div
        v-for="room in rooms"
        :key="room.id"
        class="mp-container p-3 flex flex-col gap-2"
      >
        <input
          v-model="room.name"
          @input="saveWithDebounce"
          class="w-full border border-brand-border rounded px-2 py-1 text-sm text-center"
          placeholder="Naam"
        />

        <div
          class="mt-1 px-2 py-1 text-center cursor-pointer bg-red-50 text-red-600 text-xs hover:bg-red-100"
          @click="removeRoom(room.id)"
        >
          Verwijder
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { getLockers, saveLockers } from "@/services/settings";
import { autosave } from "@/utils/autosave";

const rooms = ref([]);

onMounted(async () => {
  rooms.value = await getLockers();
});

function addRoom() {
  rooms.value.push({
    id: Date.now(),
    name: `${rooms.value.length + 1}`,
  });
  saveWithDebounce();
}

function removeRoom(id) {
  rooms.value = rooms.value.filter((r) => r.id !== id);
  saveWithDebounce();
}

function saveWithDebounce() {
  autosave("lockers", async () => {
    await saveLockers(rooms.value);
  });
}
</script>
