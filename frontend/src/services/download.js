import * as XLSX from 'xlsx'
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'

// ─── Shared data helpers ──────────────────────────────────────
function buildRows(scheduled) {
  return scheduled.map(m => ({
    'Tijd':          m.time,
    'Veld':          m.field_name,
    'Thuisteam':     m.home,
    'Uitteam':       m.away,
    'Duur (min)':    m.duration,
    'Kleedkamer thuis': m.home_locker,
    'Kleedkamer uit':   m.away_locker,
  }))
}

function filename(date, ext) {
  return `planning-${date ?? 'onbekend'}.${ext}`
}

// ─── CSV ─────────────────────────────────────────────────────
export function downloadCSV(scheduled, date) {
  const rows  = buildRows(scheduled)
  const keys  = Object.keys(rows[0])
  const lines = [
    keys.join(';'),
    ...rows.map(r => keys.map(k => `"${r[k] ?? ''}"`).join(';')),
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  trigger(blob, filename(date, 'csv'))
}

// ─── Excel ───────────────────────────────────────────────────
export function downloadExcel(scheduled, date) {
  const ws  = XLSX.utils.json_to_sheet(buildRows(scheduled))
  const wb  = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Planning')
  XLSX.writeFile(wb, filename(date, 'xlsx'))
}

// ─── PNG ─────────────────────────────────────────────────────
export async function downloadPNG(element, date) {
  const canvas = await html2canvas(element, { scale: 2, useCORS: true, backgroundColor: '#ffffff' })
  const blob   = await new Promise(res => canvas.toBlob(res, 'image/png'))
  trigger(blob, filename(date, 'png'))
}

// ─── PDF ─────────────────────────────────────────────────────
export async function downloadPDF(element, date) {
  const canvas  = await html2canvas(element, { scale: 2, useCORS: true, backgroundColor: '#ffffff' })
  const imgData = canvas.toDataURL('image/png')
  const pdf     = new jsPDF({ orientation: 'landscape', unit: 'px', format: [canvas.width / 2, canvas.height / 2] })
  pdf.addImage(imgData, 'PNG', 0, 0, canvas.width / 2, canvas.height / 2)
  pdf.save(filename(date, 'pdf'))
}

// ─── Helper ──────────────────────────────────────────────────
function trigger(blob, name) {
  const url = URL.createObjectURL(blob)
  const a   = document.createElement('a')
  a.href    = url
  a.download = name
  a.click()
  URL.revokeObjectURL(url)
}
