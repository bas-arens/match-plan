const BASE = "http://localhost:8000";

export async function getSportlinkPreview(date) {
  return fetch(`${BASE}/sportlink/get_sportlink_preview?datum=${date}`)
    .then(r => r.json());
}

export async function getMatchDates() {
  return fetch(`${BASE}/sportlink/get_match_dates`)
    .then(r => r.json());
}
