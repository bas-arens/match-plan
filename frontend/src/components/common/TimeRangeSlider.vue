<template>
  <div class="time-range-slider">

    <!-- Time labels above track -->
    <div class="flex justify-between text-xs font-medium text-brand-dark mb-3">
      <span>{{ formatMin(modelStart) }}</span>
      <span>{{ formatMin(modelEnd) }}</span>
    </div>

    <!-- Slider track -->
    <div class="relative h-2 rounded-full bg-gray-200" ref="track">

      <!-- Active range highlight -->
      <div
        class="absolute h-2 rounded-full bg-brand-primary"
        :style="{ left: startPercent + '%', width: (endPercent - startPercent) + '%' }"
      />

      <!-- Start handle -->
      <div
        class="slider-handle"
        :style="{ left: startPercent + '%' }"
        @mousedown="startDrag('start', $event)"
        @touchstart.prevent="startDrag('start', $event)"
      />

      <!-- End handle -->
      <div
        class="slider-handle"
        :style="{ left: endPercent + '%' }"
        @mousedown="startDrag('end', $event)"
        @touchstart.prevent="startDrag('end', $event)"
      />
    </div>

    <!-- Hour ticks -->
    <div class="relative mt-2 h-3">
      <span
        v-for="tick in ticks"
        :key="tick"
        class="absolute text-gray-400 text-xs transform -translate-x-1/2"
        :style="{ left: tickPercent(tick) + '%' }"
      >{{ tick }}</span>
    </div>

  </div>
</template>

<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// File:    src/components/common/TimeRangeSlider.vue
// Author:  MatchPlan
// Purpose: Dual-handle range slider for selecting a time window in minutes.
//          Supports both mouse and touch events. Used in TeamPreferences to
//          set per-team earliest/latest start times.
//
// Props:
//   modelStart  — start value in minutes since midnight (required)
//   modelEnd    — end value in minutes since midnight (required)
//   min         — minimum selectable value in minutes (default: 07:00)
//   max         — maximum selectable value in minutes (default: 23:00)
//   step        — snap interval in minutes (default: 15)
//
// Functions:
//   tickPercent      — converts an hour label to a % position on the track
//   formatMin        — formats minutes as "HH:MM"
//   snapToStep       — rounds a raw minute value to the nearest step
//   clientXFromEvent — extracts clientX from both mouse and touch events
//   onMove           — handles drag movement and emits updated values
//   onUp             — ends a drag and removes window event listeners
//   startDrag        — initiates a drag on a handle
// ─────────────────────────────────────────────────────────────────────────────
import { ref, computed, onUnmounted } from "vue"

const props = defineProps({
  modelStart: { type: Number, required: true },  // minutes
  modelEnd:   { type: Number, required: true },  // minutes
  min:        { type: Number, default: 7 * 60 },
  max:        { type: Number, default: 23 * 60 },
  step:       { type: Number, default: 15 },
})

const emit = defineEmits(["update:modelStart", "update:modelEnd", "change"])

const track = ref(null)
const dragging = ref(null)  // 'start' | 'end' | null

const range = computed(() => props.max - props.min)
const startPercent = computed(() => ((props.modelStart - props.min) / range.value) * 100)
const endPercent   = computed(() => ((props.modelEnd   - props.min) / range.value) * 100)

const ticks = computed(() => {
  const result = []
  for (let h = Math.ceil(props.min / 60); h <= Math.floor(props.max / 60); h += 2) {
    result.push(`${String(h).padStart(2, "0")}`)
  }
  return result
})

function tickPercent(hourStr) {
  return ((parseInt(hourStr) * 60 - props.min) / range.value) * 100
}

function formatMin(min) {
  const h = Math.floor(min / 60).toString().padStart(2, "0")
  const m = (min % 60).toString().padStart(2, "0")
  return `${h}:${m}`
}

function snapToStep(min) {
  return Math.round(min / props.step) * props.step
}

function clientXFromEvent(event) {
  return event.touches ? event.touches[0].clientX : event.clientX
}

function onMove(event) {
  if (!dragging.value || !track.value) return
  const rect  = track.value.getBoundingClientRect()
  const ratio = Math.min(1, Math.max(0, (clientXFromEvent(event) - rect.left) / rect.width))
  const raw   = props.min + ratio * range.value
  const val   = Math.min(props.max, Math.max(props.min, snapToStep(raw)))

  if (dragging.value === "start") {
    if (val < props.modelEnd - props.step) {
      emit("update:modelStart", val)
      emit("change")
    }
  } else {
    if (val > props.modelStart + props.step) {
      emit("update:modelEnd", val)
      emit("change")
    }
  }
}

function onUp() {
  dragging.value = null
  window.removeEventListener("mousemove", onMove)
  window.removeEventListener("mouseup",   onUp)
  window.removeEventListener("touchmove", onMove)
  window.removeEventListener("touchend",  onUp)
}

function startDrag(handle, event) {
  dragging.value = handle
  window.addEventListener("mousemove", onMove)
  window.addEventListener("mouseup",   onUp)
  window.addEventListener("touchmove", onMove)
  window.addEventListener("touchend",  onUp)
}

onUnmounted(onUp)
</script>

<style scoped>
.time-range-slider {
  padding: 0 8px;
}

.slider-handle {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 18px;
  height: 18px;
  background: white;
  border: 2px solid #00DF82;
  border-radius: 50%;
  cursor: grab;
  box-shadow: 0 1px 4px rgba(0,0,0,0.15);
  transition: box-shadow 0.15s;
  z-index: 2;
}

.slider-handle:hover,
.slider-handle:active {
  box-shadow: 0 0 0 4px #C6FFE7;
  cursor: grabbing;
}
</style>
