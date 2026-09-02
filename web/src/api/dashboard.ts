// src/api/dashboard.ts
import { useAuth } from "@/store/auth.store";

const BASE = import.meta.env.VITE_API_BASE ?? "";

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

export interface TestCaseDistribution {
  functional: number;
  negative: number;
  boundary: number;
}

export interface ApprovalStats {
  draft: number;
  approved: number;
  rejected: number;
}

export interface RecentActivity {
  date: string;
  count: number;
}

export interface DashboardStats {
  total_sessions: number;
  total_test_cases: number;
  avg_execution_time_ms: number;
  last_generation_date: string | null;
  test_case_distribution: TestCaseDistribution;
  approval_stats: ApprovalStats;
  recent_activity: RecentActivity[];
}

export async function getDashboardStats(token: string): Promise<DashboardStats> {
  const res = await fetch(`${BASE}/v1/dashboard/stats`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    handleAuthError(res.status);
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch dashboard stats");
  }

  return res.json();
}
