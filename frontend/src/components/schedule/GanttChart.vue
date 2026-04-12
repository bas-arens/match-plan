<template>
  <div
    class="gantt-wrapper"
    :class="{ 'is-dragging-active': drag.active }"
    @mousemove="onMouseMove"
    @mouseleave="onMouseLeave"
    @mouseup="onMouseUp"
  >

    <!-- TIME HEADER -->
    <div class="gantt-header-row">
      <div class="gantt-label-col"></div>
      <div class="gantt-sublane-placeholder"></div>
      <div class="gantt-timeline-header">
        <div
          v-for="hour in hours"
          :key="hour"
          class="gantt-hour-mark"
          :style="{ left: hourPercent(hour) + '%' }"
        >{{ String(hour).padStart(2, '0') }}:00</div>
      </div>
    </div>

    <!-- FIELD ROWS -->
    <div v-for="field in fields" :key="field.id" class="gantt-field-row">

      <div class="gantt-label-col">
        <span class="gantt-field-name">{{ field.name }}</span>
      </div>

      <div class="gantt-sublane-col" :style="{ height: LANES.length * LANE_H + 'px' }">
        <div
          v-for="(label, i) in LANE_LABELS"
          :key="label"
          class="gantt-sublane-label"
          :style="{ top: i * LANE_H + 'px', height: LANE_H + 'px' }"
        >{{ label }}</div>
      </div>

      <div
        class="gantt-lanes-area"
        :ref="el => { if (el) lanesAreaRefs[field.id] = el }"
        :style="{ height: LANES.length * LANE_H + 'px' }"
      >
        <!-- LANE STRIPES -->
        <div
          v-for="(lane, i) in LANES"
          :key="lane"
          class="gantt-lane-stripe"
          :style="{ top: i * LANE_H + 'px', height: LANE_H + 'px' }"
        />

        <!-- HOUR TICKS -->
        <div
          v-for="hour in hours"
          :key="'g-' + hour"
          class="gantt-tick"
          :style="{ left: hourPercent(hour) + '%' }"
        />

        <!-- DROP TARGET -->
        <div
          v-if="drag.active && drag.targetFieldId === field.id && drag.targetTime"
          class="gantt-drop-target"
          :style="dropTargetStyle"
        />

        <!-- MATCH BLOCKS -->
        <div
          v-for="m in laned.filter(m => m.field_id === field.id)"
          :key="m.match_id"
          class="gantt-block"
          :class="{ 'is-source': drag.active && drag.matchId === m.match_id }"
          :style="blockStyle(m)"
          @mousedown.prevent="onBlockMousedown(m, $event)"
          @mouseenter="!drag.active && showTooltip(m, $event)"
          @mouseleave="tooltip.visible = false"
        >
          <div class="gantt-block-bar" :style="{ backgroundColor: dotColor(m.match_id) }" />
          <div class="gantt-block-text">
            <span class="gantt-block-home">{{ m.home }}</span>
            <span class="gantt-block-meta">{{ m.time }}<span v-if="subFieldLabel(m)"> · {{ m.field_name }} {{ subFieldLabel(m) }}</span></span>
          </div>
          <div v-if="matchHasPenalty(m.match_id)" class="gantt-block-warn">!</div>
        </div>

      </div>
    </div>

    <!-- LEGEND -->
    <div class="gantt-legend">
      <div
        v-for="group in legendGroups"
        :key="group"
        class="gantt-legend-item"
      >
        <span class="gantt-legend-dot" :style="{ backgroundColor: AGE_GROUP_COLORS[group] }" />
        <span class="gantt-legend-label">{{ AGE_GROUP_LABELS[group] }}</span>
      </div>
    </div>

    <!-- PENALTY PANEL -->
    <div class="penalty-panel">
      <div class="penalty-header">
        <span class="penalty-title">PENALTIES</span>
        <span class="penalty-total" :class="penalties.total === 0 ? 'total--ok' : 'total--warn'">
          total: {{ penalties.total }}
        </span>
      </div>

      <div v-if="penalties.total === 0" class="penalty-empty">
        ● geen penalties
      </div>

      <div v-else class="penalty-list">
        <div
          v-for="(item, i) in penalties.items"
          :key="i"
          class="penalty-row"
        >
          <span class="penalty-dot" :style="{ backgroundColor: PENALTY_COLORS[item.type] }" />
          <span class="penalty-type">{{ item.type }}</span>
          <span class="penalty-label">{{ item.label }}</span>
          <span class="penalty-pts">+{{ item.points }}</span>
        </div>
      </div>
    </div>

  </div>

  <!-- GHOST -->
  <Teleport to="body">
    <div v-if="drag.active && dragMatch" class="gantt-ghost" :style="ghostStyle">
      <div class="gantt-block-bar" :style="{ backgroundColor: dotColor(dragMatch.match_id) }" />
      <div class="gantt-block-text">
        <span class="gantt-block-home">{{ dragMatch.home }}</span>
        <span class="gantt-block-meta">{{ drag.targetTime ?? dragMatch.time }}</span>
      </div>
    </div>
  </Teleport>

  <!-- TOOLTIP -->
  <Teleport to="body">
    <div
      v-if="tooltip.visible && !drag.active"
      class="gantt-tooltip"
      :style="{ top: tooltip.y + 'px', left: tooltip.x + 'px' }"
    >
      <div class="tt-line tt-home">
        {{ tooltip.match?.home }}
        <span class="tt-vs">vs</span>
        {{ tooltip.match?.away }}
      </div>
      <div class="tt-line tt-meta">
        {{ tooltip.match?.time }} · {{ tooltip.match?.duration }} min · {{ tooltip.match?.field_name }}{{ tooltip.match && subFieldLabel(tooltip.match) ? ' ' + subFieldLabel(tooltip.match) : '' }}
      </div>
      <div class="tt-line tt-lockers">
        kleedkamers: {{ tooltip.match?.home_locker }} / {{ tooltip.match?.away_locker }}
      </div>
    </div>
  </Teleport>
</template>


<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// File:    src/components/schedule/GanttChart.vue
// Author:  Bas Arens
// Purpose: Interactive Gantt chart for visualising and manually adjusting the
//          generated match planning. Supports drag-and-drop to move matches
//          between fields and time slots, with real-time penalty recalculation.
//
// Props:
//   scheduled    — array of scheduled match objects from the optimizer
//   preferences  — team time-window and field/locker preferences
//   allFields    — all configured fields (for surface penalty checks)
//   lockers      — all configured locker rooms
//
// Key functions:
//   laned           — bin-packs matches into lanes per field (computed)
//   penalties       — calculates all active penalties in real time (computed)
//   blockStyle      — returns inline style for a match block on the timeline
//   subFieldLabel   — returns A/B or A1/A2/B1/B2 for sub-field divisions
//   onBlockMousedown — starts a drag operation
//   onMouseMove     — updates ghost position and snaps drop target
//   commitDrag      — applies the drag result to localSchedule
// ─────────────────────────────────────────────────────────────────────────────
import { computed, onUnmounted, reactive, ref, watch } from 'vue'
import { timeToMin } from '@/utils/time.js'

const props = defineProps({
  scheduled:   { type: Array, required: true },
  preferences: { type: Array, default: () => [] },
  allFields:   { type: Array, default: () => [] },
  lockers:     { type: Array, default: () => [] },
  priorities:  { type: Object, default: () => ({ lockers: 1, time_windows: 1, field_preference: 1 }) },
})

// ─── CONSTANTS ───────────────────────────────────────────────
const DAY_START    = 8 * 60
const DAY_END      = 20 * 60
const DAY_DURATION = DAY_END - DAY_START
const SLOT_SIZE    = 15

const LANE_H      = 44
const LANES       = ['A', 'B', 'C', 'D']
const LANE_LABELS = ['A1', 'A2', 'B1', 'B2']
const hours       = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

const LOCKER_BUFFER_AFTER   = 30
const BASE_LOCKER_PENALTY   = 50
const BASE_FIELD_PENALTY    = 30
const BASE_WINDOW_FLAT      = 150   // flat penalty for being outside window at all
const BASE_EARLY_PER_MIN    = 0.5
const TEAM_OVERLAP_PENALTY  = 500

function inferAge(teamName) {
  const m = teamName.toUpperCase().match(/[JM]O(\d+)/)
  return m ? parseInt(m[1]) : 100
}

function lockerBufferBefore(teamName) {
  const age = inferAge(teamName)
  if (age >= 100) return 60
  if (age >= 17)  return 45
  if (age >= 13)  return 40
  return 30
}

const LOCKER_PENALTY        = computed(() => BASE_LOCKER_PENALTY * (props.priorities.lockers ?? 1))
const FIELD_PREF_PENALTY    = computed(() => BASE_FIELD_PENALTY  * (props.priorities.field_preference ?? 1))
const EARLY_PREF_PER_MIN    = computed(() => BASE_EARLY_PER_MIN  * (props.priorities.time_windows ?? 1))

const AGE_GROUP_COLORS = {
  'senioren': '#3B82F6',  // blue
  'jo7-9':    '#10B981',  // emerald  — youngest
  'jo10-12':  '#F59E0B',  // amber
  'jo13-15':  '#F43F5E',  // rose
  'jo16-19':  '#8B5CF6',  // violet
}

const AGE_GROUP_LABELS = {
  'senioren': 'Senioren',
  'jo7-9':    'JO/MO 7–9',
  'jo10-12':  'JO/MO 10–12',
  'jo13-15':  'JO/MO 13–15',
  'jo16-19':  'JO/MO 16–19',
}

function ageGroup(teamName) {
  const m = teamName.toUpperCase().match(/[JM]O(\d+)/)
  if (!m) return 'senioren'
  const age = parseInt(m[1])
  if (age <= 9)  return 'jo7-9'
  if (age <= 12) return 'jo10-12'
  if (age <= 15) return 'jo13-15'
  return 'jo16-19'
}

const PENALTY_COLORS = {
  window:      '#EAB308',
  early:       '#A3E635',
  locker:      '#F97316',
  locker_pref: '#FB923C',
  overlap:     '#EF4444',
  field:       '#8B5CF6',
}

const LOCKER_PREF_PENALTY = computed(() => 30 * (props.priorities.lockers ?? 1))

// ─── LOCAL SCHEDULE ──────────────────────────────────────────
const localSchedule = ref([...props.scheduled])

watch(() => props.scheduled, val => {
  localSchedule.value = [...val]
}, { deep: true })

// ─── HELPERS ─────────────────────────────────────────────────

function minToTime(min) {
  const clamped = Math.max(DAY_START, Math.min(DAY_END - SLOT_SIZE, min))
  const h = Math.floor(clamped / 60)
  const m = clamped % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

function laneCount(fieldSize) {
  return Math.round(fieldSize * 4)
}

function hourPercent(hour) {
  return ((hour * 60 - DAY_START) / DAY_DURATION) * 100
}

function subFieldLabel(m) {
  if (m.field_size >= 1.0) return ''
  if (m.field_size >= 0.5) return m.laneStart === 0 ? 'A' : 'B'
  return LANE_LABELS[m.laneStart] ?? ''
}

// ─── FIELDS ──────────────────────────────────────────────────
const fields = computed(() => {
  const seen = new Map()
  for (const m of localSchedule.value) {
    if (!seen.has(m.field_id)) {
      seen.set(m.field_id, { id: m.field_id, name: m.field_name })
    }
  }
  return [...seen.values()].sort((a, b) => a.name.localeCompare(b.name))
})

// ─── BIN-PACKING ─────────────────────────────────────────────
const laned = computed(() => {
  const result = []
  for (const field of fields.value) {
    const fieldMatches = localSchedule.value
      .filter(m => m.field_id === field.id)
      .sort((a, b) => timeToMin(a.time) - timeToMin(b.time))

    const laneEnd = [0, 0, 0, 0]
    for (const m of fieldMatches) {
      const start = timeToMin(m.time)
      const end   = start + m.duration
      const count = laneCount(m.field_size)
      let laneStart = 0

      // Respect manual lane override from drag-and-drop if those lanes are free
      if (m.laneOverride !== undefined) {
        const ov = m.laneOverride
        const free = [...Array(count)].every((_, k) => laneEnd[ov + k] <= start)
        if (free) {
          for (let j = ov; j < ov + count; j++) laneEnd[j] = end
          result.push({ ...m, laneStart: ov, laneCount: count })
          continue
        }
      }

      // Auto bin-packing: aligned placement
      outer: for (let i = 0; i <= 4 - count; i += count) {
        for (let j = i; j < i + count; j++) {
          if (laneEnd[j] > start) continue outer
        }
        laneStart = i
        break
      }
      for (let j = laneStart; j < laneStart + count; j++) laneEnd[j] = end
      result.push({ ...m, laneStart, laneCount: count })
    }
  }
  return result
})

// ─── COLORS ──────────────────────────────────────────────────
function dotColor(matchId) {
  const match = laned.value.find(m => m.match_id === matchId)
  return match ? AGE_GROUP_COLORS[ageGroup(match.home)] : '#9CA3AF'
}

const legendGroups = computed(() => {
  const seen = new Set(laned.value.map(m => ageGroup(m.home)))
  return Object.keys(AGE_GROUP_COLORS).filter(g => seen.has(g))
})

// ─── BLOCK STYLE ─────────────────────────────────────────────
function blockStyle(m) {
  const startMin = timeToMin(m.time)
  const left   = ((startMin - DAY_START) / DAY_DURATION) * 100
  const width  = (m.duration / DAY_DURATION) * 100
  const top    = m.laneStart * LANE_H
  const height = m.laneCount * LANE_H
  const color  = dotColor(m.match_id)
  return {
    left:            `${left}%`,
    width:           `calc(${width}% - 2px)`,
    top:             `${top + 1}px`,
    height:          `${height - 2}px`,
    cursor:          'grab',
    backgroundColor: '#F3F4F6',
    borderColor:     '#D1D5DB',
  }
}

// ─── PENALTY CALCULATION ─────────────────────────────────────
const penalties = computed(() => {
  const items = []
  let total = 0

  const sched = localSchedule.value.map(m => ({
    ...m, startMin: timeToMin(m.time), endMin: timeToMin(m.time) + m.duration,
  }))

  for (const m of sched) {
    const pref = props.preferences.find(p => p.team === m.home)
    if (!pref) continue

    const ws = timeToMin(pref.start), we = timeToMin(pref.end)
    let win = 0
    if (m.startMin < ws)    win = ws - m.startMin
    else if (m.endMin > we) win = m.endMin - we
    if (win > 0) {
      const pTime = props.priorities.time_windows ?? 1
      const winPts = (BASE_WINDOW_FLAT + win) * pTime
      total += winPts
      items.push({ type: 'window', match_id: m.match_id, points: winPts,
        label: `${m.home}: ${win} min buiten tijdvenster` })
    } else {
      // Earliness: prefer starting at the beginning of the time window
      const earlyMin = m.startMin - ws
      if (earlyMin > 0) {
        const earlyPts = Math.round(earlyMin * EARLY_PREF_PER_MIN.value * 10) / 10
        if (earlyPts > 0) {
          total += earlyPts
          items.push({ type: 'early', match_id: m.match_id, points: earlyPts,
            label: `${m.home}: ${earlyMin} min na vroegst mogelijke start` })
        }
      }
    }

    const preferredIds = pref.preferred_field_ids ?? []
    if (preferredIds.length > 0 && !preferredIds.includes(m.field_id)) {
      total += FIELD_PREF_PENALTY.value
      items.push({ type: 'field', match_id: m.match_id, points: FIELD_PREF_PENALTY.value,
        label: `${m.home}: niet op voorkeursveld` })
    }

    // Locker preference (home locker only)
    const preferredLockers = pref.preferred_locker_ids ?? []
    if (preferredLockers.length > 0 && m.home_locker != null &&
        !preferredLockers.includes(m.home_locker)) {
      total += LOCKER_PREF_PENALTY.value
      items.push({ type: 'locker_pref', match_id: m.match_id, points: LOCKER_PREF_PENALTY.value,
        label: `${m.home}: niet op voorkeurskleedkamer` })
    }
  }

  for (let i = 0; i < sched.length; i++) {
    for (let j = i + 1; j < sched.length; j++) {
      const a = sched[i], b = sched[j]
      if (a.startMin < b.endMin && b.startMin < a.endMin) {
        const clash = a.home === b.home || a.home === b.away ||
                      a.away === b.home || a.away === b.away
        if (clash) {
          total += TEAM_OVERLAP_PENALTY
          items.push({ type: 'overlap', match_id: a.match_id, points: TEAM_OVERLAP_PENALTY,
            label: `${a.home} & ${b.home}: team speelt tegelijk` })
        }
      }
    }
  }

  // Locker sharing (pair-based, symmetric: 50 × priority per shared locker
  // between two matches whose locker windows overlap).
  if (props.lockers.length >= 2) {
    const withLockerWindow = sched.map(m => ({
      ...m,
      lk_start: m.startMin - lockerBufferBefore(m.home),
      lk_end:   m.endMin   + LOCKER_BUFFER_AFTER,
    }))
    for (let i = 0; i < withLockerWindow.length; i++) {
      for (let j = i + 1; j < withLockerWindow.length; j++) {
        const a = withLockerWindow[i]
        const b = withLockerWindow[j]
        if (!(a.lk_start < b.lk_end && b.lk_start < a.lk_end)) continue
        const aSet = new Set([a.home_locker, a.away_locker].filter(x => x != null))
        const bSet = new Set([b.home_locker, b.away_locker].filter(x => x != null))
        let shared = 0
        for (const lk of aSet) if (bSet.has(lk)) shared++
        if (shared > 0) {
          const pts = LOCKER_PENALTY.value * shared
          total += pts
          items.push({ type: 'locker', match_id: a.match_id, points: pts,
            label: `${a.home} & ${b.home}: kleedkamer gedeeld` })
        }
      }
    }
  }

  return { total, items }
})

const penaltyMatchIds = computed(() => new Set(penalties.value.items.map(p => p.match_id)))
function matchHasPenalty(id) { return penaltyMatchIds.value.has(id) }

// ─── DRAG ────────────────────────────────────────────────────
const lanesAreaRefs = {}
const drag = reactive({
  active: false, matchId: null,
  mouseX: 0, mouseY: 0,
  targetFieldId: null, targetTime: null, targetLane: 0,
})

const dragMatch = computed(() =>
  drag.matchId ? laned.value.find(m => m.match_id === drag.matchId) : null
)

function onBlockMousedown(m, event) {
  drag.active = true; drag.matchId = m.match_id
  drag.mouseX = event.clientX; drag.mouseY = event.clientY
  drag.targetFieldId = m.field_id; drag.targetTime = m.time
  drag.targetLane = m.laneStart ?? 0
  tooltip.visible = false
  window.addEventListener('mouseup', commitDrag, { once: true })
}

function onMouseMove(event) {
  drag.mouseX = event.clientX; drag.mouseY = event.clientY
  if (!drag.active) { positionTooltip(event); return }
  for (const f of fields.value) {
    const el = lanesAreaRefs[f.id]
    if (!el) continue
    const rect = el.getBoundingClientRect()
    if (event.clientY >= rect.top && event.clientY <= rect.bottom) {
      drag.targetFieldId = f.id
      // Horizontal: snap to time slot
      const fracX   = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width))
      const snapped = Math.round((DAY_START + fracX * DAY_DURATION) / SLOT_SIZE) * SLOT_SIZE
      drag.targetTime = minToTime(snapped)
      // Vertical: snap to aligned lane for this match's size
      const count   = dragMatch.value?.laneCount ?? 1
      const fracY   = Math.max(0, Math.min(0.999, (event.clientY - rect.top) / rect.height))
      const rawLane = Math.floor(fracY * LANES.length)
      drag.targetLane = Math.min(Math.floor(rawLane / count) * count, LANES.length - count)
      break
    }
  }
}

function onMouseLeave() { tooltip.visible = false }
function onMouseUp()    { commitDrag() }

function commitDrag() {
  if (drag.active && drag.targetFieldId && drag.targetTime) {
    const idx = localSchedule.value.findIndex(m => m.match_id === drag.matchId)
    if (idx !== -1) {
      const field = fields.value.find(f => f.id === drag.targetFieldId)
        ?? props.allFields.find(f => f.id === drag.targetFieldId)
      localSchedule.value[idx] = {
        ...localSchedule.value[idx],
        field_id: drag.targetFieldId,
        field_name: field?.name ?? drag.targetFieldId,
        time: drag.targetTime,
        laneOverride: drag.targetLane,
      }
    }
  }
  drag.active = false; drag.matchId = null
  window.removeEventListener('mouseup', commitDrag)
}

onUnmounted(() => {
  window.removeEventListener('mouseup', commitDrag)
})

const ghostStyle = computed(() => {
  if (!drag.active || !dragMatch.value) return { display: 'none' }
  return {
    position: 'fixed',
    left: drag.mouseX + 'px', top: drag.mouseY + 'px',
    transform: 'translate(-6px, -10px)',
    width: '200px', height: `${LANE_H - 2}px`,
    zIndex: 9999, pointerEvents: 'none',
  }
})

const dropTargetStyle = computed(() => {
  if (!drag.active || !drag.targetTime || !dragMatch.value) return {}
  const m = dragMatch.value
  const left  = ((timeToMin(drag.targetTime) - DAY_START) / DAY_DURATION) * 100
  const width = (m.duration / DAY_DURATION) * 100
  return {
    position: 'absolute',
    left: `${left}%`, width: `calc(${width}% - 2px)`,
    top: `${drag.targetLane * LANE_H + 1}px`, height: `${m.laneCount * LANE_H - 2}px`,
    background: 'rgba(0,0,0,0.04)',
    border: '1px dashed #9CA3AF',
    borderRadius: '2px',
    zIndex: 1, pointerEvents: 'none',
  }
})

// ─── TOOLTIP ─────────────────────────────────────────────────
const tooltip = reactive({ visible: false, x: 0, y: 0, match: null })

function showTooltip(m, event) {
  tooltip.match = m; tooltip.visible = true; positionTooltip(event)
}

function positionTooltip(event) {
  tooltip.x = event.clientX + 14; tooltip.y = event.clientY + 14
}
</script>


<style scoped>
/* ─── BASE ──────────────────────────────────────────────── */
.gantt-wrapper {
  font-family: 'JetBrains Mono', 'Cascadia Code', 'Fira Code', ui-monospace, monospace;
  font-size: 11px;
  user-select: none;
  color: #111827;
}

.is-dragging-active { cursor: grabbing; }

/* ─── HEADER ────────────────────────────────────────────── */
.gantt-header-row {
  display: flex;
  height: 24px;
  margin-bottom: 4px;
}

.gantt-sublane-placeholder {
  width: 28px;
  min-width: 28px;
}

.gantt-timeline-header {
  flex: 1;
  position: relative;
}

.gantt-hour-mark {
  position: absolute;
  transform: translateX(-50%);
  color: #9CA3AF;
  font-size: 10px;
  white-space: nowrap;
}

/* ─── FIELD ROWS ────────────────────────────────────────── */
.gantt-field-row {
  display: flex;
  margin-bottom: 2px;
  border-top: 1px solid #F3F4F6;
}

.gantt-field-row:first-of-type {
  border-top: none;
}

.gantt-label-col {
  width: 80px;
  min-width: 80px;
  display: flex;
  align-items: center;
  padding: 0 8px 0 0;
  position: relative;
}

/* Short horizontal stub from field name — stops at the elbow, never crosses vertical lines */
.gantt-label-col::after {
  content: '';
  position: absolute;
  right: 12px;
  top: 50%;
  width: 16px;
  height: 1px;
  background: #D1D5DB;
}

.gantt-field-name {
  font-size: 11px;
  font-weight: 700;
  color: #374151;
  white-space: nowrap;
}

/* ─── SUB-LANE LABELS ───────────────────────────────────── */
.gantt-sublane-col {
  width: 28px;
  min-width: 28px;
  position: relative;
  border-right: 1px solid #F3F4F6;
}

.gantt-sublane-label {
  position: absolute;
  left: 0; right: 0;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding-left: 14px;
  font-size: 9px;
  font-weight: 600;
  color: #374151;
}

/* Horizontal segment of each L-shape */
.gantt-sublane-label::before {
  content: '';
  position: absolute;
  left: -12px;
  top: 50%;
  width: 20px;
  height: 1px;
  background: #D1D5DB;
}

/* Vertical segment of each L-shape — connects to field name center (row midpoint) */
.gantt-sublane-label::after {
  content: '';
  position: absolute;
  left: -12px;
  width: 1px;
  background: #D1D5DB;
}

/* A1: 1.5 lanes above center → vertical goes DOWN 66px to row center */
.gantt-sublane-label:nth-child(1)::after {
  top: 50%;
  height: 66px;
}
/* A2: 0.5 lanes above center → vertical goes DOWN 22px to row center */
.gantt-sublane-label:nth-child(2)::after {
  top: 50%;
  height: 22px;
}
/* B1: 0.5 lanes below center → vertical goes UP 22px to row center */
.gantt-sublane-label:nth-child(3)::after {
  bottom: 50%;
  height: 22px;
}
/* B2: 1.5 lanes below center → vertical goes UP 66px to row center */
.gantt-sublane-label:nth-child(4)::after {
  bottom: 50%;
  height: 66px;
}

/* ─── LANES AREA ────────────────────────────────────────── */
.gantt-lanes-area {
  flex: 1;
  position: relative;
}

.gantt-lane-stripe {
  position: absolute;
  left: 0; right: 0;
  border-bottom: 1px solid #F9FAFB;
}

.gantt-lane-stripe:nth-child(even) {
  background: rgba(0,0,0,0.01);
}

.gantt-tick {
  position: absolute;
  top: 0; bottom: 0;
  width: 1px;
  background: #F3F4F6;
  z-index: 0;
}

/* ─── MATCH BLOCK ───────────────────────────────────────── */
.gantt-block {
  position: absolute;
  display: flex;
  align-items: stretch;
  border: 1px solid;
  border-radius: 2px;
  z-index: 2;
  overflow: hidden;
  transition: filter 0.1s, opacity 0.1s;
}

.gantt-block:hover {
  filter: brightness(0.95);
  z-index: 10;
}

.gantt-block.is-source {
  opacity: 0.2;
}

.gantt-block-bar {
  width: 3px;
  flex-shrink: 0;
}

.gantt-block-text {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 2px 5px;
  overflow: hidden;
  flex: 1;
  gap: 1px;
}

.gantt-block-home {
  font-size: 10px;
  font-weight: 700;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gantt-block-meta {
  font-size: 9px;
  color: #9CA3AF;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gantt-block-warn {
  position: absolute;
  top: 3px; right: 3px;
  width: 12px; height: 12px;
  background: #F97316;
  color: white;
  border-radius: 50%;
  font-size: 8px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ─── GHOST ─────────────────────────────────────────────── */
.gantt-ghost {
  font-family: 'JetBrains Mono', 'Cascadia Code', ui-monospace, monospace;
  font-size: 11px;
  display: flex;
  align-items: stretch;
  background: white;
  border: 1px solid #D1D5DB;
  border-left: none;
  border-radius: 2px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  opacity: 0.95;
}

/* ─── LEGEND ────────────────────────────────────────────── */
.gantt-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #E5E7EB;
}

.gantt-legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.gantt-legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.gantt-legend-label {
  font-size: 10px;
  color: #6B7280;
}

/* ─── PENALTY PANEL ─────────────────────────────────────── */
.penalty-panel {
  margin-top: 20px;
  border-top: 1px solid #E5E7EB;
  padding-top: 12px;
  font-family: 'JetBrains Mono', 'Cascadia Code', ui-monospace, monospace;
}

.penalty-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 8px;
}

.penalty-title {
  font-size: 10px;
  font-weight: 700;
  color: #9CA3AF;
  letter-spacing: 0.08em;
}

.penalty-total {
  font-size: 12px;
  font-weight: 700;
}

.total--ok   { color: #059669; }
.total--warn { color: #111827; }

.penalty-empty {
  font-size: 11px;
  color: #059669;
}

.penalty-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.penalty-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #374151;
}

.penalty-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.penalty-type {
  width: 52px;
  flex-shrink: 0;
  color: #9CA3AF;
  font-size: 10px;
}

.penalty-label {
  flex: 1;
  color: #374151;
}

.penalty-pts {
  font-weight: 700;
  color: #111827;
  white-space: nowrap;
}

/* ─── TOOLTIP ───────────────────────────────────────────── */
.gantt-tooltip {
  position: fixed;
  z-index: 9999;
  background: #111827;
  color: #F9FAFB;
  border-radius: 6px;
  padding: 10px 14px;
  pointer-events: none;
  font-family: 'JetBrains Mono', 'Cascadia Code', ui-monospace, monospace;
  font-size: 11px;
  line-height: 1.6;
  white-space: nowrap;
  box-shadow: 0 4px 20px rgba(0,0,0,0.25);
}

.tt-home {
  font-weight: 700;
  font-size: 12px;
  margin-bottom: 4px;
}

.tt-vs {
  font-weight: 400;
  color: #6B7280;
  margin: 0 4px;
}

.tt-meta, .tt-lockers {
  color: #9CA3AF;
  font-size: 10px;
}
</style>
