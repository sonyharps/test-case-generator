// src/api/orchestrator.ts
const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

function getAuthHeaders(token?: string | null): HeadersInit {
  const headers: HeadersInit = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export async function runOrchestrator(payload: any, token: string) {
  const res = await fetch(`${BASE}/v1/orchestrator/run`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Orchestrator error: ${res.status} ${txt}`);
  }
  return res.json();
}

export async function downloadOrchestratorPdf(payload: any, token: string) {
  const res = await fetch(`${BASE}/v1/orchestrator/pdf`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`PDF export failed: ${res.status} ${txt}`);
  }
  const blob = await res.blob();
  return blob;
}

export async function downloadSessionPdf(sessionId: string, token: string) {
  const res = await fetch(`${BASE}/v1/orchestrator/pdf`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`PDF export failed: ${res.status} ${txt}`);
  }
  const blob = await res.blob();
  return blob;
}
