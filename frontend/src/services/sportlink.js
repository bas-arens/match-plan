const BASE = "http://127.0.0.1:8000/sportlink";

/* ---------------------------------------------------
   📌 1. Clubgegevens
--------------------------------------------------- */
export async function getClubGegevens() {
  const r = await fetch(`${BASE}/clubgegevens`);
  return r.json();
}

/* ---------------------------------------------------
   📌 2. Heel programma (alle wedstrijden)
--------------------------------------------------- */
export async function getProgramma() {
  const r = await fetch(`${BASE}/programma`);
  return r.json();
}

/* ---------------------------------------------------
   📌 3. Programma op datum (alle thuiswedstrijden op 1 dag)
--------------------------------------------------- */
export async function getProgrammaOpDatum(date) {
  const r = await fetch(`${BASE}/programma/datum?datum=${date}`);
  return r.json();
}

/* ---------------------------------------------------
   📌 4. Lijst met datums waarop thuis wordt gespeeld
--------------------------------------------------- */
export async function getDatumLijst() {
  const r = await fetch(`${BASE}/programma/datumlijst`);
  return r.json();
}

/* ---------------------------------------------------
   📌 5. Wedstrijd-informatie (veldtype, kleedkamers, officials)
--------------------------------------------------- */
export async function getWedstrijdInfo(code) {
  const r = await fetch(`${BASE}/wedstrijd/${code}`);
  return r.json();
}

/* ---------------------------------------------------
   📌 6. Wedstrijd-statistieken (winpercentages etc.)
--------------------------------------------------- */
export async function getWedstrijdStatistieken(code) {
  const r = await fetch(`${BASE}/wedstrijd-statistieken/${code}`);
  return r.json();
}

export async function getTeams() {
  const r = await fetch(`${BASE}/teams`);
  return r.json();
}
