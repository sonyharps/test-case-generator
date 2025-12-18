// src/api/orchestrator.ts
const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function runOrchestrator(payload: any) {
  const res = await fetch(`${BASE}/v1/orchestrator/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Orchestrator error: ${res.status} ${txt}`);
  }
  return res.json();
}

export async function downloadOrchestratorPdf(payload: any) {
  const res = await fetch(`${BASE}/v1/orchestrator/pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`PDF export failed: ${res.status} ${txt}`);
  }
  const blob = await res.blob();
  return blob;
}
