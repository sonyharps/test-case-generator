// src/api/analytics.ts
const BASE = import.meta.env.VITE_API_BASE ?? "";

function getAuthHeaders(token: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export interface UserStats {
  total_sessions: number;
  total_test_cases: number;
  total_functional: number;
  total_negative: number;
  total_boundary: number;
  avg_execution_time_ms: number;
  most_used_model: string | null;
  sessions_last_30_days: number;
}

export interface TimelineDataPoint {
  date: string;
  count: number;
}

export interface TimelineResponse {
  timeline: TimelineDataPoint[];
  days: number;
}

export interface ModelUsageDataPoint {
  model: string;
  count: number;
}

export interface ModelUsageResponse {
  model_usage: ModelUsageDataPoint[];
}

export interface TestCaseBreakdown {
  functional: number;
  negative: number;
  boundary: number;
}

export async function getUserStats(token: string): Promise<UserStats> {
  const res = await fetch(`${BASE}/v1/analytics/stats`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch user statistics");
  }

  return res.json();
}

export async function getTimeline(
  token: string,
  days: number = 30
): Promise<TimelineResponse> {
  const res = await fetch(`${BASE}/v1/analytics/timeline?days=${days}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch timeline data");
  }

  return res.json();
}

export async function getModelUsage(
  token: string
): Promise<ModelUsageResponse> {
  const res = await fetch(`${BASE}/v1/analytics/models`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch model usage data");
  }

  return res.json();
}

export async function getTestCaseBreakdown(
  token: string
): Promise<TestCaseBreakdown> {
  const res = await fetch(`${BASE}/v1/analytics/test-cases/breakdown`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch test case breakdown");
  }

  return res.json();
}
