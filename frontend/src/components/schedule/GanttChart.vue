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
      <div class="gantt-field-label-col"></div>
      <div class="gantt-sublane-placeholder"></div>
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

      <!-- SUB-FIELD LABEL COLUMN -->
      <div class="gantt-sublane-col" :style="{ height: LANES.length * LANE_H + 'px' }">
        <div
          v-for="(label, i) in LANE_LABELS"
          :key="label"
          class="gantt-sublane-label"
          :style="{ top: i * LANE_H + 'px', height: LANE_H + 'px' }"
        >
          {{ label }}
        </div>
      </div>

      <!-- LANES AREA -->
      <div
        class="gantt-lanes-area"
        :ref="el => { if (el) lanesAreaRefs[field.id] = el }"
        :style="{ height: LANES.length * LANE_H + 'px' }"
      >

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
          class="gantt-match-block"
          :class="{ 'is-source': drag.active && drag.matchId === m.match_id }"
          :style="blockStyle(m)"
          @mousedown.prevent="onBlockMousedown(m, $event)"
          @mouseenter="!drag.active && showTooltip(m, $event)"
          @mouseleave="tooltip.visible = false"
        >
          <div class="gantt-match-accent" :style="{ backgroundColor: accentColor(m.match_id) }" />
          <div class="gantt-match-inner">
            <span class="gantt-match-time">
              {{ m.time }}
              <span v-if="subFieldLabel(m)" class="gantt-match-sublabel"> · {{ m.field_name }} {{ subFieldLabel(m) }}</span>
            </span>
            <span class="gantt-match-home">{{ m.home }}</span>
            <span class="gantt-match-away">{{ m.away }}</span>
          </div>
          <div v-if="matchHasPenalty(m.match_id)" class="gantt-penalty-badge">!</div>
        </div>

      </div>
    </div>

    <!-- PENALTY PANEL -->
    <div class="penalty-panel" :class="{ 'penalty-panel--ok': penalties.total === 0 }">
      <div class="penalty-panel-header">
        <div class="penalty-score" :class="penalties.total === 0 ? 'score--ok' : 'score--warn'">
          <span v-if="penalties.total === 0">✓ Geen penalties</span>
          <span v-else>⚠ Totale penalty: <strong>{{ penalties.total }}</strong></span>
        </div>
        <span v-if="drag.active" class="penalty-hint">Versleep een wedstrijd om te optimaliseren</span>
      </div>
      <div v-if="penalties.items.length > 0" class="penalty-list">
        <div
          v-for="(item, i) in penalties.items"
          :key="i"
          class="penalty-item"
          :class="`penalty-item--${item.type}`"
        >
          <span class="penalty-item-dot" />
          <span class="penalty-item-label">{{ item.label }}</span>
          <span class="penalty-item-points">+{{ item.points }}</span>
        </div>
      </div>
    </div>

  </div>

  <!-- GHOST BLOCK (follows cursor while dragging) -->
  <Teleport to="body">
    <div
      v-if="drag.active && dragMatch"
      class="gantt-ghost"
      :style="ghostStyle"
    >
      <div class="gantt-match-accent" :style="{ backgroundColor: accentColor(dragMatch.match_id) }" />
      <div class="gantt-match-inner">
        <span class="gantt-match-time">{{ drag.targetTime ?? dragMatch.time }}</span>
        <span class="gantt-match-home">{{ dragMatch.home }}</span>
        <span class="gantt-match-away">{{ dragMatch.away }}</span>
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
          <span>{{ tooltip.match?.field_name }}{{ tooltip.match && subFieldLabel(tooltip.match) ? ' ' + subFieldLabel(tooltip.match) : '' }}</span>
        </div>
        <div class="gantt-tooltip-row">
          <span class="gantt-tooltip-label">Kleedkamers</span>
          <span>{{ tooltip.match?.home_locker }} / {{ tooltip.match?.away_locker }}</span>
        </div>
      </div>
    </div>
  </Teleport>
</template>


<script setup>
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  scheduled:   { type: Array, required: true },
  preferences: { type: Array, default: () => [] },
  allFields:   { type: Array, default: () => [] },
  lockers:     { type: Array, default: () => [] },
})

// ─── CONSTANTS ───────────────────────────────────────────────
const DAY_START    = 8 * 60
const DAY_END      = 20 * 60
const DAY_DURATION = DAY_END - DAY_START
const SLOT_SIZE    = 15

const LANE_H      = 52
const LANES       = ['A', 'B', 'C', 'D']
const LANE_LABELS = ['A1', 'A2', 'B1', 'B2']
const hours       = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

const LOCKER_BUFFER          = 20
const LOCKER_PENALTY         = 50
const FIELD_PREF_PENALTY     = 30
const SURFACE_AVOID_PENALTY  = 40
const TEAM_OVERLAP_PENALTY   = 500

// ─── LOCAL SCHEDULE ──────────────────────────────────────────
const localSchedule = ref([...props.scheduled])

watch(() => props.scheduled, val => {
  localSchedule.value = [...val]
}, { deep: true })

// ─── HELPERS ─────────────────────────────────────────────────
function toMin(t) {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}

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

// ─── FIELDS (derived from local schedule) ────────────────────
const fields = computed(() => {
  const seen = new Map()
  for (const m of localSchedule.value) {
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
    const fieldMatches = localSchedule.value
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

// ─── PENALTY CALCULATION ─────────────────────────────────────
const penalties = computed(() => {
  const items = []
  let total = 0

  const sched = localSchedule.value.map(m => ({
    ...m,
    startMin: toMin(m.time),
    endMin:   toMin(m.time) + m.duration,
  }))

  // Per-match: window, field preference, surface
  for (const m of sched) {
    const pref = props.preferences.find(p => p.team === m.home)
    if (!pref) continue

    const ws = toMin(pref.start)
    const we = toMin(pref.end)
    let win = 0
    if (m.startMin < ws)      win = ws - m.startMin
    else if (m.startMin > we) win = m.startMin - we
    if (win > 0) {
      total += win
      items.push({ type: 'window', match_id: m.match_id, points: win,
        label: `${m.home}: ${win} min buiten tijdvenster` })
    }

    const preferredIds = pref.preferred_field_ids ?? []
    if (preferredIds.length > 0 && !preferredIds.includes(m.field_id)) {
      total += FIELD_PREF_PENALTY
      items.push({ type: 'field', match_id: m.match_id, points: FIELD_PREF_PENALTY,
        label: `${m.home}: niet op voorkeursveld` })
    }

    const avoidSurfaces = pref.avoid_surfaces ?? []
    const field = props.allFields.find(f => f.id === m.field_id)
    if (field && avoidSurfaces.includes(field.surface)) {
      total += SURFACE_AVOID_PENALTY
      items.push({ type: 'surface', match_id: m.match_id, points: SURFACE_AVOID_PENALTY,
        label: `${m.home}: speelt op vermeden ondergrond (${field.surface})` })
    }
  }

  // Team overlaps
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

  // Locker sharing simulation
  if (props.lockers.length >= 2) {
    const placed = []
    const sorted = [...sched].sort((a, b) => a.startMin - b.startMin)

    for (const m of sorted) {
      const lkStart = m.startMin - LOCKER_BUFFER
      const lkEnd   = m.endMin   + LOCKER_BUFFER

      const free = props.lockers.filter(lk =>
        !placed.some(p =>
          (p.home_locker === lk.id || p.away_locker === lk.id) &&
          p.lk_start < lkEnd && p.lk_start + p.lk_dur > lkStart
        )
      )

      let penalty = 0
      let homeLk, awayLk
      if (free.length >= 2) {
        ;[homeLk, awayLk] = free
      } else if (free.length === 1) {
        homeLk  = free[0]
        awayLk  = props.lockers.find(lk => lk.id !== homeLk.id)
        penalty = LOCKER_PENALTY
      } else {
        ;[homeLk, awayLk] = props.lockers
        penalty = LOCKER_PENALTY * 2
      }

      if (penalty > 0) {
        total += penalty
        items.push({ type: 'locker', match_id: m.match_id, points: penalty,
          label: `${m.home}: kleedkamer gedeeld` })
      }

      placed.push({
        home_locker: homeLk.id, away_locker: awayLk.id,
        lk_start: lkStart, lk_dur: lkEnd - lkStart,
      })
    }
  }

  return { total, items }
})

const penaltyMatchIds = computed(() => new Set(penalties.value.items.map(p => p.match_id)))

function matchHasPenalty(matchId) {
  return penaltyMatchIds.value.has(matchId)
}

// ─── DRAG ────────────────────────────────────────────────────
const lanesAreaRefs = {}

const drag = reactive({
  active:        false,
  matchId:       null,
  mouseX:        0,
  mouseY:        0,
  targetFieldId: null,
  targetTime:    null,
})

const dragMatch = computed(() =>
  drag.matchId ? laned.value.find(m => m.match_id === drag.matchId) : null
)

function onBlockMousedown(m, event) {
  drag.active        = true
  drag.matchId       = m.match_id
  drag.mouseX        = event.clientX
  drag.mouseY        = event.clientY
  drag.targetFieldId = m.field_id
  drag.targetTime    = m.time
  tooltip.visible    = false
  window.addEventListener('mouseup', commitDrag, { once: true })
}

function onMouseMove(event) {
  drag.mouseX = event.clientX
  drag.mouseY = event.clientY

  if (!drag.active) {
    positionTooltip(event)
    return
  }

  for (const f of fields.value) {
    const el = lanesAreaRefs[f.id]
    if (!el) continue
    const rect = el.getBoundingClientRect()
    if (event.clientY >= rect.top && event.clientY <= rect.bottom) {
      drag.targetFieldId = f.id
      const relX    = event.clientX - rect.left
      const frac    = Math.max(0, Math.min(1, relX / rect.width))
      const rawMin  = DAY_START + frac * DAY_DURATION
      const snapped = Math.round(rawMin / SLOT_SIZE) * SLOT_SIZE
      drag.targetTime = minToTime(snapped)
      break
    }
  }
}

function onMouseLeave() {
  tooltip.visible = false
}

function onMouseUp() {
  commitDrag()
}

function commitDrag() {
  if (drag.active && drag.targetFieldId && drag.targetTime) {
    const idx = localSchedule.value.findIndex(m => m.match_id === drag.matchId)
    if (idx !== -1) {
      const field = fields.value.find(f => f.id === drag.targetFieldId)
        ?? props.allFields.find(f => f.id === drag.targetFieldId)
      localSchedule.value[idx] = {
        ...localSchedule.value[idx],
        field_id:   drag.targetFieldId,
        field_name: field?.name ?? drag.targetFieldId,
        time:       drag.targetTime,
      }
    }
  }
  drag.active  = false
  drag.matchId = null
  window.removeEventListener('mouseup', commitDrag)
}

const ghostStyle = computed(() => {
  if (!drag.active || !dragMatch.value) return { display: 'none' }
  const colors = colorMap.value[drag.matchId]
  return {
    position:         'fixed',
    left:             drag.mouseX + 'px',
    top:              drag.mouseY + 'px',
    width:            '180px',
    height:           '52px',
    zIndex:           9999,
    pointerEvents:    'none',
    transform:        'translate(-8px, -12px)',
    borderRadius:     '6px',
    border:           '1px solid',
    overflow:         'hidden',
    display:          'flex',
    backgroundColor:  colors?.bg  ?? '#F3F4F6',
    borderColor:      colors?.border ?? '#D1D5DB',
    boxShadow:        '0 4px 20px rgba(0,0,0,0.20)',
    opacity:          '0.92',
  }
})

const dropTargetStyle = computed(() => {
  if (!drag.active || !drag.targetTime || !dragMatch.value) return {}
  const m = dragMatch.value
  const startMin = toMin(drag.targetTime)
  const left  = ((startMin - DAY_START) / DAY_DURATION) * 100
  const width = (m.duration / DAY_DURATION) * 100
  return {
    position:     'absolute',
    left:         `${left}%`,
    width:        `calc(${width}% - 3px)`,
    top:          '2px',
    height:       `${LANES.length * LANE_H - 4}px`,
    background:   'rgba(59, 130, 246, 0.08)',
    border:       '2px dashed #3B82F6',
    borderRadius: '6px',
    zIndex:       1,
    pointerEvents:'none',
  }
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
    backgroundColor: colors?.bg  ?? '#F3F4F6',
    borderColor:     colors?.border ?? '#D1D5DB',
    cursor:          'grab',
  }
}

// ─── TOOLTIP ─────────────────────────────────────────────────
const tooltip = reactive({ visible: false, x: 0, y: 0, match: null })

function showTooltip(m, event) {
  tooltip.match   = m
  tooltip.visible = true
  positionTooltip(event)
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

.is-dragging-active {
  cursor: grabbing;
}

/* HEADER */
.gantt-header-row {
  display: flex;
  height: 28px;
  margin-bottom: 6px;
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

/* SUB-FIELD LABEL COLUMN */
.gantt-sublane-col {
  width: 28px;
  min-width: 28px;
  position: relative;
  border-right: 1px solid #E5E7EB;
  background: #F9FAFB;
}

.gantt-sublane-label {
  position: absolute;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 600;
  color: #9CA3AF;
  border-bottom: 1px solid #F3F4F6;
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
  display: flex;
  transition: filter 0.1s, box-shadow 0.1s, opacity 0.1s;
}

.gantt-match-block:hover {
  filter: brightness(0.97);
  box-shadow: 0 2px 8px rgba(0,0,0,0.10);
  z-index: 10;
}

.gantt-match-block.is-source {
  opacity: 0.25;
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

.gantt-match-sublabel {
  font-weight: 400;
  color: #9CA3AF;
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

/* GHOST BLOCK */
.gantt-ghost {
  font-family: 'Inter', system-ui, sans-serif;
  font-size: 12px;
  user-select: none;
}

/* ─── PENALTY PANEL ─────────────────────────────────────── */
.penalty-panel {
  margin-top: 16px;
  border-radius: 12px;
  border: 1px solid #FED7AA;
  background: #FFF7ED;
  overflow: hidden;
}

.penalty-panel--ok {
  border-color: #A7F3D0;
  background: #F0FDF4;
}

.penalty-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
}

.penalty-score {
  font-size: 13px;
  font-weight: 600;
}

.score--warn { color: #C2410C; }
.score--ok   { color: #065F46; }

.penalty-hint {
  font-size: 11px;
  color: #9CA3AF;
  font-style: italic;
}

.penalty-list {
  border-top: 1px solid #FED7AA;
  display: flex;
  flex-direction: column;
}

.penalty-panel--ok .penalty-list {
  border-top-color: #A7F3D0;
}

.penalty-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-bottom: 1px solid rgba(0,0,0,0.04);
  font-size: 12px;
  color: #374151;
}

.penalty-item-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
  background: #F97316;
}

.penalty-item--overlap .penalty-item-dot  { background: #EF4444; }
.penalty-item--window  .penalty-item-dot  { background: #F59E0B; }
.penalty-item--locker  .penalty-item-dot  { background: #F97316; }
.penalty-item--field   .penalty-item-dot  { background: #8B5CF6; }
.penalty-item--surface .penalty-item-dot  { background: #06B6D4; }

.penalty-item-label {
  flex: 1;
}

.penalty-item-points {
  font-size: 11px;
  font-weight: 700;
  color: #9A3412;
  white-space: nowrap;
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
</style>
