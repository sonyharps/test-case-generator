// src/api/llm.ts
const BASE = import.meta.env.VITE_API_BASE || "";

function getAuthHeaders(token?: string | null): HeadersInit {
  const headers: HeadersInit = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export async function fetchLLMModels(token?: string) {
  // Use /health endpoint which queries actual Ollama models
  const res = await fetch(`${BASE}/v1/llm/health`, {
    headers: token ? getAuthHeaders(token) : {},
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch models: ${res.status}`);
  }
  const data = await res.json();

  // Transform health response to models format
  const ollamaModels = data.ollama?.available_models || [];

  // Convert to expected format with descriptions
  const models = ollamaModels.map((modelId: string) => ({
    id: modelId,
    name: modelId,
    description: "Ollama model",
  }));

  return {
    ollama: {
      provider: "ollama",
      type: "local",
      models: models,
    },
  };
}

export async function fetchLLMHealth(token?: string) {
  const res = await fetch(`${BASE}/v1/llm/health`, {
    headers: token ? getAuthHeaders(token) : {},
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch health: ${res.status}`);
  }
  return res.json();
}
