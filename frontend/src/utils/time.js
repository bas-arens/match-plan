export function timeToMin(t) {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}

export function minToTime(min) {
  return `${String(Math.floor(min / 60)).padStart(2, '0')}:${String(min % 60).padStart(2, '0')}`
}
