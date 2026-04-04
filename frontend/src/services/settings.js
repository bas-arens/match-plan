const BASE = "http://127.0.0.1:8000/settings";

/* -----------------------------
   🟩 FIELDS
----------------------------- */
export async function getFields() {
  const res = await fetch(`${BASE}/fields`);
  return await res.json();
}

export async function saveFields(fields) {
  await fetch(`${BASE}/fields`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(fields),
  });
}

/* -----------------------------
   🟦 LOCKER ROOMS
----------------------------- */
export async function getLockers() {
  const res = await fetch(`${BASE}/lockers`);
  return await res.json();
}

export async function saveLockers(lockers) {
  await fetch(`${BASE}/lockers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(lockers),
  });
}

/* -----------------------------
   🟧 TEAM PREFERENCES
----------------------------- */
export async function getPreferences() {
  const res = await fetch(`${BASE}/preferences`);
  return await res.json();
}

export async function savePreferences(preferences) {
  await fetch(`${BASE}/preferences`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(preferences),
  });
}

/* -----------------------------
   🟪 OPTIMIZER SETTINGS
----------------------------- */
export async function getOptimizer() {
  const res = await fetch(`${BASE}/optimizer`);
  return await res.json();
}

export async function saveOptimizer(settings) {
  await fetch(`${BASE}/optimizer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });
}
