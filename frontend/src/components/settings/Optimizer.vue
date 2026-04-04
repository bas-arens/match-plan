<template>
  <div class="mp-container space-y-3">
    <h2 class="text-xl font-semibold">Optimizer instellingen</h2>

    <label class="text-sm text-gray-600">Kies algoritme</label>
    <select
      v-model="algo"
      @change="saveWithDebounce"
      class="w-full px-3 py-2 border border-brand-border rounded text-sm"
    >
      <option value="milp">MILP</option>
      <option value="greedy">Greedy</option>
      <option value="sa">Simulated Annealing</option>
    </select>

    <div class="text-xs text-gray-500">
      Dit wordt gebruikt als standaard oplosmethode.
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { getOptimizer, saveOptimizer } from "@/services/settings";
import { autosave } from "@/utils/autosave";

const algo = ref("milp");

onMounted(async () => {
  const data = await getOptimizer();
  algo.value = data.algorithm;
});

function saveWithDebounce() {
  autosave("optimizer", async () => {
    await saveOptimizer({ algorithm: algo.value });
  });
}
</script>
