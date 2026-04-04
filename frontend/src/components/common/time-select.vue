<template>
  <select
    v-model="model"
    @change="$emit('update:modelValue', model)"
    class="w-full px-2 py-1 border border-brand-border rounded text-sm bg-white"
  >
    <option
      v-for="t in times"
      :key="t"
      :value="t"
    >
      {{ t }}
    </option>
  </select>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  modelValue: { type: String, required: true },
});

const emit = defineEmits(["update:modelValue"]);

/* Internal model */
const model = computed({
  get: () => props.modelValue,
  set: (val) => emit("update:modelValue", val),
});

/* Generate times: 00, 15, 30, 45 for each hour */
const times = [];
for (let h = 0; h < 24; h++) {
  for (let m of ["00", "15", "30", "45"]) {
    const hh = h.toString().padStart(2, "0");
    times.push(`${hh}:${m}`);
  }
}
</script>
