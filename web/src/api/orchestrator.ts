// src/api/orchestrator.ts
const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

// Timeout for local Ollama models (8 sequential calls can take 10-15 min)
const ORCHESTRATOR_TIMEOUT_MS = 900000; // 15 minutes

function getAuthHeaders(token?: string | null): HeadersInit {
  const headers: HeadersInit = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

// Helper function to create timeout with AbortController
function createTimeout(ms: number): AbortSignal {
  const controller = new AbortController();
  setTimeout(() => controller.abort(), ms);
  return controller.signal;
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
      throw new Error(`Request timeout: Local LLM took too long (8 API calls). Try a faster model or wait longer.`);
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

export async function getCapacityStats(token: string) {
  const res = await fetch(`${BASE}/v1/orchestrator/capacity`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Capacity stats failed: ${res.status} ${txt}`);
  }
  return res.json();
}

export interface CapacityStats {
  active_users: number;
  max_concurrent_users: number;
  capacity_percent: number;
  available_slots: number;
  status: "healthy" | "busy" | "full";
  batching_enabled: boolean;
  api_calls_per_generation: number;
  optimization_note: string;
}
