// src/api/orchestrator.ts
const BASE = import.meta.env.VITE_API_BASE ?? "";

// Timeout for local Ollama models (qwen3:4b may be slower, 4-5 min)
const ORCHESTRATOR_TIMEOUT_MS = 360000; // 6 minutes

function getAuthHeaders(token?: string | null): HeadersInit {
  const headers: HeadersInit = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export async function runOrchestrator(payload: any, token: string) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), ORCHESTRATOR_TIMEOUT_MS);

  try {
    console.log("[Orchestrator API] Starting request with payload:", {
      mode: payload.llm_config?.mode,
      requirement: payload.requirement?.substring(0, 50) + "...",
    });

    const res = await fetch(`${BASE}/v1/orchestrator/run`, {
      method: "POST",
      headers: getAuthHeaders(token),
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    console.log("[Orchestrator API] Response status:", res.status, res.statusText);

    if (!res.ok) {
      const txt = await res.text();
      console.error("[Orchestrator API] Error response:", txt);
      throw new Error(`Orchestrator error: ${res.status} ${txt}`);
    }

    const data = await res.json();
    console.log("[Orchestrator API] Success, received:", {
      hasSummary: !!data.summary,
      functionalCount: data.functional?.length || 0,
      negativeCount: data.negative?.length || 0,
      boundaryCount: data.boundary?.length || 0,
    });

    return data;
  } catch (err: any) {
    clearTimeout(timeoutId);

    if (err.name === "AbortError") {
      console.error("[Orchestrator API] Request timed out after", ORCHESTRATOR_TIMEOUT_MS, "ms");
      throw new Error(`Request timeout: The server took too long to respond. Try using Local LLM mode for faster results.`);
    }

    console.error("[Orchestrator API] Request failed:", err);
    throw err;
  }
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

export async function downloadOrchestratorExcel(payload: any, token: string) {
  const res = await fetch(`${BASE}/v1/orchestrator/excel`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Excel export failed: ${res.status} ${txt}`);
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

export async function downloadSessionExcel(sessionId: string, token: string) {
  const res = await fetch(`${BASE}/v1/orchestrator/excel`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Excel export failed: ${res.status} ${txt}`);
  }
  const blob = await res.blob();
  return blob;
}
