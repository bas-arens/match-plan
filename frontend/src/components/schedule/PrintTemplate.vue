<template>
  <div class="print-root">

    <!-- HEADER -->
    <div class="print-header">
      <div class="print-brand">
        <!-- Logo placeholder — replace img src when logo is ready -->
        <div class="print-logo-placeholder">M</div>
        <span class="print-brand-name">MatchPlan</span>
      </div>
      <div class="print-meta">
        <div class="print-meta-date">{{ formattedDate }}</div>
        <div class="print-meta-algo">{{ algorithm }}</div>
      </div>
    </div>

    <div class="print-divider" />

    <!-- SECTION TITLE -->
    <div class="print-section-title">Speeldag planning</div>

    <!-- SCHEDULE TABLE -->
    <table class="print-table">
      <thead>
        <tr>
          <th>Tijd</th>
          <th>Veld</th>
          <th>Thuisteam</th>
          <th>Uitteam</th>
          <th>Duur</th>
          <th>Kleedkamer thuis</th>
          <th>Kleedkamer uit</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="m in sortedSchedule"
          :key="m.match_id"
          :class="{ 'row-warning': m.penalty > 0 }"
        >
          <td class="col-time">{{ m.time }}</td>
          <td>{{ m.field_name }}</td>
          <td class="col-team">{{ m.home }}</td>
          <td class="col-team">{{ m.away }}</td>
          <td class="col-dur">{{ m.duration }} min</td>
          <td>{{ m.home_locker }}</td>
          <td>
            {{ m.away_locker }}
            <span v-if="m.penalty > 0" class="warn-tag">gedeeld</span>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- FOOTER -->
    <div class="print-footer">
      <span>Gegenereerd door MatchPlan</span>
      <span>{{ formattedDate }}</span>
    </div>

  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  scheduled: { type: Array, required: true },
  date:      { type: String, default: null  },
  algorithm: { type: String, default: ''    },
})

const sortedSchedule = computed(() =>
  [...props.scheduled].sort((a, b) => a.time.localeCompare(b.time))
)

const formattedDate = computed(() => {
  if (!props.date) return ''
  return new Date(props.date).toLocaleDateString('nl-NL', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
  })
})
</script>

<style scoped>
/* All fonts are system fonts — no web font loading, html2canvas safe */
.print-root {
  width: 1100px;
  padding: 48px 56px;
  background: #ffffff;
  font-family: 'Helvetica Neue', Arial, sans-serif;
  color: #111827;
  box-sizing: border-box;
}

/* HEADER */
.print-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.print-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.print-logo-placeholder {
  width: 36px;
  height: 36px;
  background: #111827;
  color: white;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 800;
  font-family: 'Helvetica Neue', Arial, sans-serif;
}

.print-brand-name {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.5px;
  color: #111827;
}

.print-meta {
  text-align: right;
}

.print-meta-date {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  text-transform: capitalize;
}

.print-meta-algo {
  font-size: 11px;
  color: #9CA3AF;
  margin-top: 2px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* DIVIDER */
.print-divider {
  height: 2px;
  background: #111827;
  margin-bottom: 24px;
}

/* SECTION TITLE */
.print-section-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #9CA3AF;
  margin-bottom: 12px;
}

/* TABLE */
.print-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  font-family: 'Courier New', Courier, monospace;
}

.print-table thead tr {
  border-bottom: 1px solid #111827;
}

.print-table th {
  text-align: left;
  padding: 6px 12px 6px 0;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #6B7280;
  font-family: 'Helvetica Neue', Arial, sans-serif;
}

.print-table td {
  padding: 7px 12px 7px 0;
  border-bottom: 1px solid #F3F4F6;
  color: #111827;
  vertical-align: middle;
}

.print-table tr.row-warning td {
  background: #FFFBEB;
}

.col-time { font-weight: 700; white-space: nowrap; }
.col-team { font-weight: 500; }
.col-dur  { color: #9CA3AF; }

.warn-tag {
  margin-left: 6px;
  font-size: 9px;
  color: #F97316;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* FOOTER */
.print-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 32px;
  padding-top: 12px;
  border-top: 1px solid #E5E7EB;
  font-size: 10px;
  color: #9CA3AF;
  font-family: 'Helvetica Neue', Arial, sans-serif;
}
</style>
