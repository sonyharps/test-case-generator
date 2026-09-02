// src/api/users.ts
import { useAuth } from "@/store/auth.store";

const BASE = import.meta.env.VITE_API_BASE ?? "";

function getAuthHeaders(token: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export interface UserListItem {
  id: number;
  username: string;
  email: string;
  full_name?: string | null;
  is_active: boolean;
  role: string;
  squad_id?: number | null;
  squad_name?: string | null;
  created_at: string;
}

export interface UserListResponse {
  users: UserListItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface UserUpdatePayload {
  role?: string;
  is_active?: boolean;
  squad_id?: number | null;
  full_name?: string;
  email?: string;
}

export async function listUsers(
  token: string,
  params?: { search?: string; role?: string; squad_id?: number; is_active?: boolean; skip?: number; limit?: number }
): Promise<UserListResponse> {
  const qs = new URLSearchParams();
  if (params?.search) qs.set("search", params.search);
  if (params?.role) qs.set("role", params.role);
  if (params?.squad_id !== undefined) qs.set("squad_id", String(params.squad_id));
  if (params?.is_active !== undefined) qs.set("is_active", String(params.is_active));
  if (params?.skip !== undefined) qs.set("skip", String(params.skip));
  if (params?.limit !== undefined) qs.set("limit", String(params.limit));
  const q = qs.toString() ? `?${qs.toString()}` : "";

  const res = await fetch(`${BASE}/v1/users${q}`, { headers: getAuthHeaders(token) });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Failed to list users: ${res.status} ${txt}`);
  }
  return res.json();
}

export async function updateUser(
  userId: number,
  payload: UserUpdatePayload,
  token: string
): Promise<UserListItem> {
  const res = await fetch(`${BASE}/v1/users/${userId}`, {
    method: "PATCH",
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Failed to update user: ${res.status} ${txt}`);
  }
  return res.json();
}

export async function deleteUser(userId: number, token: string): Promise<void> {
  const res = await fetch(`${BASE}/v1/users/${userId}`, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });
  if (!res.ok && res.status !== 204) {
    const txt = await res.text();
    throw new Error(`Failed to delete user: ${res.status} ${txt}`);
  }
}

/** Convenience helper used outside React hooks (returns current token). */
export function getToken(): string | null {
  return useAuth.getState().accessToken;
}
