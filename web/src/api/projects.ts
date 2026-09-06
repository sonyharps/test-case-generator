// src/api/projects.ts
const BASE = import.meta.env.VITE_API_BASE ?? "";

export interface ProjectItem {
  id: number;
  name: string;
  code?: string | null;
  description?: string | null;
  is_active: boolean;
  session_count: number;
  test_case_count: number;
  squads: { id: number; name: string }[];
  created_at: string;
}

function headers(token?: string | null): HeadersInit {
  const h: HeadersInit = { "Content-Type": "application/json" };
  if (token) (h as Record<string, string>).Authorization = `Bearer ${token}`;
  return h;
}

export async function listProjects(token: string | null): Promise<ProjectItem[]> {
  const res = await fetch(`${BASE}/v1/projects`, { headers: headers(token) });
  if (!res.ok) throw new Error(`Failed to load projects: ${res.status}`);
  return res.json();
}

export async function createProject(
  data: { name: string; code?: string; description?: string },
  token: string | null
): Promise<ProjectItem> {
  const res = await fetch(`${BASE}/v1/projects`, {
    method: "POST",
    headers: headers(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error((await res.text()) || "Failed to create project");
  return res.json();
}

export async function deleteProject(id: number, token: string | null): Promise<void> {
  const res = await fetch(`${BASE}/v1/projects/${id}`, {
    method: "DELETE",
    headers: headers(token),
  });
  if (!res.ok) throw new Error(`Failed to delete project: ${res.status}`);
}

// Squad → project mapping (admin sets this once; QA projects follow their squad)
export async function setSquadProject(
  squadId: number,
  projectId: number | null,
  token: string | null
): Promise<void> {
  const res = await fetch(`${BASE}/v1/squads/${squadId}`, {
    method: "PATCH",
    headers: headers(token),
    body: JSON.stringify({ project_id: projectId }),
  });
  if (!res.ok) throw new Error((await res.text()) || "Failed to update squad");
}
