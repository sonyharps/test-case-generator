// src/api/squads.ts
const BASE = import.meta.env.VITE_API_BASE ?? "";

function getAuthHeaders(token: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export interface SquadItem {
  id: number;
  name: string;
  description?: string | null;
  member_count: number;
  project_id?: number | null;
  project_name?: string | null;
  created_at: string;
}

export interface SquadListResponse {
  squads: SquadItem[];
  total: number;
}

export interface SquadMember {
  id: number;
  username: string;
  email: string;
  full_name?: string | null;
  role: string;
  is_active: boolean;
}

export interface SquadDetail extends SquadItem {
  members: SquadMember[];
}

export async function listSquads(token: string): Promise<SquadListResponse> {
  const res = await fetch(`${BASE}/v1/squads`, { headers: getAuthHeaders(token) });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Failed to list squads: ${res.status} ${txt}`);
  }
  return res.json();
}

export async function createSquad(
  payload: { name: string; description?: string },
  token: string
): Promise<SquadItem> {
  const res = await fetch(`${BASE}/v1/squads`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Failed to create squad: ${res.status} ${txt}`);
  }
  return res.json();
}

export async function updateSquad(
  squadId: number,
  payload: { name?: string; description?: string },
  token: string
): Promise<SquadItem> {
  const res = await fetch(`${BASE}/v1/squads/${squadId}`, {
    method: "PATCH",
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Failed to update squad: ${res.status} ${txt}`);
  }
  return res.json();
}

export async function deleteSquad(squadId: number, token: string): Promise<void> {
  const res = await fetch(`${BASE}/v1/squads/${squadId}`, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });
  if (!res.ok && res.status !== 204) {
    const txt = await res.text();
    throw new Error(`Failed to delete squad: ${res.status} ${txt}`);
  }
}

export async function getSquadMembers(squadId: number, token: string): Promise<SquadDetail> {
  const res = await fetch(`${BASE}/v1/squads/${squadId}/members`, {
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Failed to get squad members: ${res.status} ${txt}`);
  }
  return res.json();
}
