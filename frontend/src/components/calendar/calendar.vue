<template>
  <div class="cal">

    <!-- NAVIGATION -->
    <div class="cal-nav">
      <button class="cal-nav-btn" @click="prevMonth">‹</button>
      <span class="cal-month-label">{{ monthLabel }}</span>
      <button class="cal-nav-btn" @click="nextMonth">›</button>
    </div>

    <!-- DAY HEADERS -->
    <div class="cal-grid">
      <span v-for="d in DAY_HEADERS" :key="d" class="cal-header-cell">{{ d }}</span>

      <!-- LEADING BLANKS -->
      <span v-for="i in leadingBlanks" :key="'b' + i" />

      <!-- DAY CELLS -->
      <button
        v-for="day in daysInMonth"
        :key="day"
        class="cal-day"
        :class="{
          'is-today':    isToday(day),
          'is-selected': isSelected(day),
          'has-matches': hasMatches(day),
        }"
        @click="selectDay(day)"
      >
        <span class="cal-day-num">{{ day }}</span>
        <span v-if="hasMatches(day)" class="cal-dot" />
      </button>
    </div>

    <!-- FOOTER -->
    <div class="cal-footer">
      <button class="cal-today-btn" @click="goToday">vandaag</button>
      <span v-if="selectedDate" class="cal-match-count">
        <template v-if="matches.length > 0">
          {{ matches.length }} {{ matches.length === 1 ? 'wedstrijd' : 'wedstrijden' }}
        </template>
        <template v-else>geen wedstrijden</template>
      </span>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { getDatumLijst, getProgrammaOpDatum } from '@/services/sportlink.js'

const props = defineProps({ modelValue: Array })
const emit  = defineEmits(['update:modelValue', 'dateSelected'])

const DAY_HEADERS = ['ma', 'di', 'wo', 'do', 'vr', 'za', 'zo']

const today         = new Date()
const currentYear   = ref(today.getFullYear())
const currentMonth  = ref(today.getMonth())  // 0-indexed
const selectedDate  = ref(null)
const availableDates = ref([])
const matches        = ref(props.modelValue ?? [])

// ─── MONTH LABEL ─────────────────────────────────────────────
const MONTHS = ['januari','februari','maart','april','mei','juni',
                'juli','augustus','september','oktober','november','december']

const monthLabel = computed(() =>
  `${MONTHS[currentMonth.value]} ${currentYear.value}`
)

// ─── GRID HELPERS ────────────────────────────────────────────
const daysInMonth = computed(() =>
  new Date(currentYear.value, currentMonth.value + 1, 0).getDate()
)

const leadingBlanks = computed(() => {
  const day = new Date(currentYear.value, currentMonth.value, 1).getDay()
  return (day + 6) % 7  // Monday = 0
})

// ─── STATE CHECKS ────────────────────────────────────────────
function isoForDay(day) {
  const m = String(currentMonth.value + 1).padStart(2, '0')
  const d = String(day).padStart(2, '0')
  return `${currentYear.value}-${m}-${d}`
}

function isToday(day) {
  return isoForDay(day) === toISO(today)
}

function isSelected(day) {
  return selectedDate.value && isoForDay(day) === toISO(selectedDate.value)
}

function hasMatches(day) {
  return availableDates.value.includes(isoForDay(day))
}

function toISO(d) {
  return d.toLocaleDateString('sv-SE')
}

// ─── NAVIGATION ──────────────────────────────────────────────
function prevMonth() {
  if (currentMonth.value === 0) { currentMonth.value = 11; currentYear.value-- }
  else currentMonth.value--
}

function nextMonth() {
  if (currentMonth.value === 11) { currentMonth.value = 0; currentYear.value++ }
  else currentMonth.value++
}

function goToday() {
  currentYear.value  = today.getFullYear()
  currentMonth.value = today.getMonth()
  selectDay(today.getDate())
}

// ─── SELECT ──────────────────────────────────────────────────
async function selectDay(day) {
  selectedDate.value = new Date(currentYear.value, currentMonth.value, day)
  const iso = isoForDay(day)
  emit('dateSelected', selectedDate.value)
  const result = await getProgrammaOpDatum(iso)
  matches.value = result
  emit('update:modelValue', result)
}

// ─── INIT ────────────────────────────────────────────────────
onMounted(async () => {
  const raw = await getDatumLijst()
  availableDates.value = raw  // already ISO strings from API
  await selectDay(today.getDate())
})
</script>

<style scoped>
.cal {
  font-family: 'JetBrains Mono', 'Cascadia Code', ui-monospace, monospace;
  user-select: none;
}

/* NAVIGATION */
.cal-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.cal-nav-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #9CA3AF;
  background: none;
  border: none;
  cursor: pointer;
  border-radius: 4px;
  transition: color 0.15s, background 0.15s;
  line-height: 1;
}

.cal-nav-btn:hover {
  color: #111827;
  background: #F3F4F6;
}

.cal-month-label {
  font-size: 13px;
  font-weight: 700;
  color: #111827;
  text-transform: lowercase;
}

/* GRID */
.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}

.cal-header-cell {
  text-align: center;
  font-size: 9px;
  font-weight: 600;
  color: #D1D5DB;
  padding-bottom: 6px;
  text-transform: lowercase;
}

/* DAY CELL */
.cal-day {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 48px;
  background: none;
  border: none;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.1s;
  gap: 2px;
}

.cal-day:hover {
  background: #F3F4F6;
}

.cal-day-num {
  font-size: 11px;
  color: #374151;
  line-height: 1;
}

.cal-day.is-today .cal-day-num {
  color: #111827;
  font-weight: 700;
}

.cal-day.is-selected {
  background: #111827;
}

.cal-day.is-selected .cal-day-num {
  color: #ffffff;
  font-weight: 700;
}

.cal-day.is-selected .cal-dot {
  background: #9CA3AF;
}

/* MATCH DOT */
.cal-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #00DF82;
  flex-shrink: 0;
}

/* FOOTER */
.cal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid #F3F4F6;
}

.cal-today-btn {
  font-family: inherit;
  font-size: 10px;
  font-weight: 600;
  color: #9CA3AF;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  text-transform: lowercase;
  letter-spacing: 0.05em;
  transition: color 0.15s;
}

.cal-today-btn:hover {
  color: #111827;
}

.cal-match-count {
  font-size: 10px;
  color: #9CA3AF;
}
</style>
