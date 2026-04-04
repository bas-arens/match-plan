const BASE = "http://127.0.0.1:8000/optimize";

export async function runOptimizer(date) {
  const res = await fetch(`${BASE}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ date })
  });
  return res.json();
}
