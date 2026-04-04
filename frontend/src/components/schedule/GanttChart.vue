<template>
  <div class="gantt-wrapper" @mousemove="onMouseMove" @mouseleave="tooltip.visible = false">

    <!-- TIME HEADER -->
    <div class="gantt-header-row">
      <div class="gantt-field-label-col"></div>
      <div class="gantt-timeline-header">
        <div
          v-for="hour in hours"
          :key="hour"
          class="gantt-hour-mark"
          :style="{ left: hourPercent(hour) + '%' }"
        >
          {{ String(hour).padStart(2, '0') }}:00
        </div>
      </div>
    </div>

    <!-- ONE SECTION PER FIELD -->
    <div v-for="field in fields" :key="field.id" class="gantt-field-section">

      <!-- FIELD LABEL -->
      <div class="gantt-field-label-col">
        <span class="gantt-field-name">{{ field.name }}</span>
        <span class="gantt-field-surface">{{ field.surface || '' }}</span>
      </div>

      <!-- LANES AREA -->
      <div class="gantt-lanes-area" :style="{ height: LANES.length * LANE_H + 'px' }">

        <!-- LANE BACKGROUNDS -->
        <div
          v-for="(lane, i) in LANES"
          :key="lane"
          class="gantt-lane-row"
          :style="{ top: i * LANE_H + 'px', height: LANE_H + 'px' }"
        />

        <!-- HOUR GRID LINES -->
        <div
          v-for="hour in hours"
          :key="'grid-' + hour"
          class="gantt-grid-line"
          :style="{ left: hourPercent(hour) + '%' }"
        />

        <!-- MATCH BLOCKS -->
        <div
          v-for="m in laned.filter(m => m.field_id === field.id)"
          :key="m.match_id"
          class="gantt-match-block"
          :style="blockStyle(m)"
          @mouseenter="showTooltip(m, $event)"
          @mouseleave="tooltip.visible = false"
        >
          <!-- Left accent bar -->
          <div class="gantt-match-accent" :style="{ backgroundColor: accentColor(m.match_id) }" />

          <div class="gantt-match-inner">
            <span class="gantt-match-time">{{ m.time }}</span>
            <span class="gantt-match-home">{{ m.home }}</span>
            <span class="gantt-match-away">{{ m.away }}</span>
          </div>

          <!-- Penalty badge -->
          <div v-if="m.penalty > 0" class="gantt-penalty-badge">!</div>
        </div>

      </div>
    </div>

    <!-- TOOLTIP -->
    <Teleport to="body">
      <div
        v-if="tooltip.visible"
        class="gantt-tooltip"
        :style="{ top: tooltip.y + 'px', left: tooltip.x + 'px' }"
      >
        <div class="gantt-tooltip-header">
          <span class="gantt-tooltip-home">{{ tooltip.match?.home }}</span>
          <span class="gantt-tooltip-sep">vs</span>
          <span class="gantt-tooltip-away">{{ tooltip.match?.away }}</span>
        </div>
        <div class="gantt-tooltip-rows">
          <div class="gantt-tooltip-row">
            <span class="gantt-tooltip-label">Tijd</span>
            <span>{{ tooltip.match?.time }} · {{ tooltip.match?.duration }} min</span>
          </div>
          <div class="gantt-tooltip-row">
            <span class="gantt-tooltip-label">Veld</span>
            <span>{{ tooltip.match?.field_name }}</span>
          </div>
          <div class="gantt-tooltip-row">
            <span class="gantt-tooltip-label">Kleedkamers</span>
            <span>{{ tooltip.match?.home_locker }} / {{ tooltip.match?.away_locker }}</span>
          </div>
          <div v-if="tooltip.match?.penalty > 0" class="gantt-tooltip-warning">
            ⚠ Kleedkamer gedeeld
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { computed, reactive } from 'vue'

const props = defineProps({
  scheduled: { type: Array, required: true },
})

// ─── CONSTANTS ───────────────────────────────────────────────
const DAY_START    = 8 * 60
const DAY_END      = 20 * 60
const DAY_DURATION = DAY_END - DAY_START

const LANE_H = 52
const LANES  = ['A', 'B', 'C', 'D']
const hours  = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

// ─── HELPERS ─────────────────────────────────────────────────
function toMin(t) {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}

function laneCount(fieldSize) {
  return Math.round(fieldSize * 4)
}

function hourPercent(hour) {
  return ((hour * 60 - DAY_START) / DAY_DURATION) * 100
}

// ─── FIELDS ──────────────────────────────────────────────────
const fields = computed(() => {
  const seen = new Map()
  for (const m of props.scheduled) {
    if (!seen.has(m.field_id)) {
      seen.set(m.field_id, {
        id:      m.field_id,
        name:    m.field_name,
        surface: m.field_surface ?? null,
      })
    }
  }
  return [...seen.values()].sort((a, b) => a.name.localeCompare(b.name))
})

// ─── LANE BIN-PACKING ────────────────────────────────────────
const laned = computed(() => {
  const result = []

  for (const field of fields.value) {
    const fieldMatches = props.scheduled
      .filter(m => m.field_id === field.id)
      .sort((a, b) => toMin(a.time) - toMin(b.time))

    const laneEnd = [0, 0, 0, 0]

    for (const m of fieldMatches) {
      const start = toMin(m.time)
      const end   = start + m.duration
      const count = laneCount(m.field_size)

      let laneStart = 0
      outer: for (let i = 0; i <= 4 - count; i++) {
        for (let j = i; j < i + count; j++) {
          if (laneEnd[j] > start) continue outer
        }
        laneStart = i
        break
      }

      for (let j = laneStart; j < laneStart + count; j++) {
        laneEnd[j] = end
      }

      result.push({ ...m, laneStart, laneCount: count })
    }
  }

  return result
})

// ─── COLORS ──────────────────────────────────────────────────
const PALETTE = [
  { bg: '#EFF6FF', border: '#3B82F6' },
  { bg: '#F5F3FF', border: '#8B5CF6' },
  { bg: '#ECFDF5', border: '#10B981' },
  { bg: '#FFFBEB', border: '#F59E0B' },
  { bg: '#FFF1F2', border: '#F43F5E' },
  { bg: '#ECFEFF', border: '#06B6D4' },
  { bg: '#FDF4FF', border: '#D946EF' },
  { bg: '#F7FEE7', border: '#84CC16' },
]

const colorMap = computed(() => {
  const map = {}
  props.scheduled.forEach((m, i) => {
    map[m.match_id] = PALETTE[i % PALETTE.length]
  })
  return map
})

function accentColor(matchId) {
  return colorMap.value[matchId]?.border ?? '#6B7280'
}

// ─── BLOCK STYLE ─────────────────────────────────────────────
function blockStyle(m) {
  const startMin = toMin(m.time)
  const left   = ((startMin - DAY_START) / DAY_DURATION) * 100
  const width  = (m.duration / DAY_DURATION) * 100
  const top    = m.laneStart * LANE_H
  const height = m.laneCount * LANE_H
  const colors = colorMap.value[m.match_id]

  return {
    left:            `${left}%`,
    width:           `calc(${width}% - 3px)`,
    top:             `${top + 2}px`,
    height:          `${height - 4}px`,
    backgroundColor: colors?.bg ?? '#F3F4F6',
    borderColor:     colors?.border ?? '#D1D5DB',
  }
}

// ─── TOOLTIP ─────────────────────────────────────────────────
const tooltip = reactive({ visible: false, x: 0, y: 0, match: null })

function showTooltip(m, event) {
  tooltip.match   = m
  tooltip.visible = true
  positionTooltip(event)
}

function onMouseMove(event) {
  if (tooltip.visible) positionTooltip(event)
}

function positionTooltip(event) {
  tooltip.x = event.clientX + 16
  tooltip.y = event.clientY + 16
}
</script>

<style scoped>
.gantt-wrapper {
  font-family: 'Inter', system-ui, sans-serif;
  font-size: 12px;
  user-select: none;
  overflow-x: auto;
}

/* HEADER */
.gantt-header-row {
  display: flex;
  height: 28px;
  margin-bottom: 6px;
}

.gantt-timeline-header {
  flex: 1;
  position: relative;
}

.gantt-hour-mark {
  position: absolute;
  transform: translateX(-50%);
  color: #9CA3AF;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
}

/* FIELD SECTION */
.gantt-field-section {
  display: flex;
  margin-bottom: 8px;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  overflow: hidden;
  background: white;
}

/* FIELD LABEL COLUMN */
.gantt-field-label-col {
  width: 88px;
  min-width: 88px;
  background: #F9FAFB;
  border-right: 1px solid #E5E7EB;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px 6px;
  gap: 3px;
}

.gantt-field-name {
  font-weight: 700;
  font-size: 13px;
  color: #111827;
  text-align: center;
}

.gantt-field-surface {
  font-size: 10px;
  color: #9CA3AF;
  text-transform: capitalize;
  text-align: center;
}

/* LANES AREA */
.gantt-lanes-area {
  flex: 1;
  position: relative;
}

/* LANE ROW */
.gantt-lane-row {
  position: absolute;
  left: 0;
  right: 0;
  border-bottom: 1px solid #F3F4F6;
}

.gantt-lane-row:nth-child(even) {
  background: #FAFAFA;
}

/* GRID LINES */
.gantt-grid-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 1px;
  background: #E5E7EB;
  z-index: 0;
}

/* MATCH BLOCK */
.gantt-match-block {
  position: absolute;
  border-radius: 6px;
  border: 1px solid;
  z-index: 2;
  overflow: hidden;
  cursor: default;
  display: flex;
  transition: filter 0.15s, box-shadow 0.15s;
}

.gantt-match-block:hover {
  filter: brightness(0.97);
  box-shadow: 0 2px 8px rgba(0,0,0,0.10);
  z-index: 10;
}

/* LEFT ACCENT */
.gantt-match-accent {
  width: 3px;
  flex-shrink: 0;
}

/* MATCH CONTENT */
.gantt-match-inner {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 3px 6px;
  overflow: hidden;
  flex: 1;
  gap: 1px;
}

.gantt-match-time {
  font-size: 9px;
  font-weight: 600;
  color: #6B7280;
  white-space: nowrap;
}

.gantt-match-home {
  font-size: 11px;
  font-weight: 700;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gantt-match-away {
  font-size: 10px;
  color: #6B7280;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* PENALTY BADGE */
.gantt-penalty-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 14px;
  height: 14px;
  background: #F97316;
  color: white;
  border-radius: 50%;
  font-size: 9px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* TOOLTIP */
.gantt-tooltip {
  position: fixed;
  z-index: 9999;
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  padding: 12px 14px;
  min-width: 220px;
  pointer-events: none;
  font-family: 'Inter', system-ui, sans-serif;
}

.gantt-tooltip-header {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #F3F4F6;
}

.gantt-tooltip-home {
  font-weight: 700;
  font-size: 13px;
  color: #111827;
}

.gantt-tooltip-sep {
  font-size: 11px;
  color: #9CA3AF;
}

.gantt-tooltip-away {
  font-size: 12px;
  color: #4B5563;
}

.gantt-tooltip-rows {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.gantt-tooltip-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #374151;
  gap: 12px;
}

.gantt-tooltip-label {
  color: #9CA3AF;
  font-weight: 500;
  white-space: nowrap;
}

.gantt-tooltip-warning {
  margin-top: 6px;
  font-size: 11px;
  color: #F97316;
  font-weight: 600;
}
</style>
