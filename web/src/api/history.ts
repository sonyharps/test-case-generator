// src/api/history.ts
import { useAuth } from "@/store/auth.store";

const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

function getAuthHeaders(token: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

// Helper to handle auth errors
function handleAuthError(status: number) {
  if (status === 401) {
    // Token expired - logout user
    useAuth.getState().logout();
    window.location.href = "/login";
  }
}

export interface SessionSummary {
  id: number;
  session_id: string;
  requirement_text: string;
  model_used: string;
  generate_boundary: boolean;
  include_risk: boolean;
  execution_time_ms: number;
  created_at: string;
  test_case_count: number;
}

export interface SessionListResponse {
  sessions: SessionSummary[];
  total: number;
  skip: number;
  limit: number;
}

export interface TestCase {
  id: number;  // Database ID for editing
  tc_id: string;
  title: string;
  preconditions: string[];
  steps: string[];
  expected_result: string[];
  status?: "draft" | "approved" | "rejected";  // Phase 2: approval status
  edit_count?: number;
  edited_by?: string | null;
  edited_at?: string | null;
}

export interface SessionDetail {
  session_id: string;
  requirement_text: string;
  model_used: string;
  generate_boundary: boolean;
  include_risk: boolean;
  execution_time_ms: number;
  created_at: string;
  functional: TestCase[];
  negative: TestCase[];
  boundary: TestCase[];
  summary: any;
  risk: any;
  coverage_matrix: any;
  metadata: any;
}

export async function getSessionList(
  token: string,
  skip: number = 0,
  limit: number = 20
): Promise<SessionListResponse> {
  const res = await fetch(`${BASE}/v1/history/sessions?skip=${skip}&limit=${limit}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    handleAuthError(res.status);
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch sessions");
  }

  return res.json();
}

export async function getSessionDetail(
  token: string,
  sessionId: string
): Promise<SessionDetail> {
  const res = await fetch(`${BASE}/v1/history/sessions/${sessionId}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    handleAuthError(res.status);
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch session detail");
  }

  return res.json();
}

export async function deleteSession(token: string, sessionId: string): Promise<void> {
  const res = await fetch(`${BASE}/v1/history/sessions/${sessionId}`, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    handleAuthError(res.status);
    const error = await res.json();
    throw new Error(error.detail || "Failed to delete session");
  }
}
