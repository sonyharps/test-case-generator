// src/api/requirements.ts
const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

function getAuthHeaders(token: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export interface Requirement {
  id: number;
  user_id: number;
  title: string;
  description: string;
  tags: string | null;
  is_template: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface RequirementCreate {
  title: string;
  description: string;
  tags?: string;
  is_template?: boolean;
}

export interface RequirementUpdate {
  title?: string;
  description?: string;
  tags?: string;
  is_template?: boolean;
}

export interface RequirementListResponse {
  requirements: Requirement[];
  total: number;
  skip: number;
  limit: number;
}

export async function createRequirement(
  data: RequirementCreate,
  token: string
): Promise<Requirement> {
  const res = await fetch(`${BASE}/v1/requirements`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to create requirement");
  }

  return res.json();
}

export async function getRequirements(
  token: string,
  skip: number = 0,
  limit: number = 20,
  search?: string,
  isTemplate?: boolean,
  tags?: string
): Promise<RequirementListResponse> {
  const params = new URLSearchParams();
  params.append("skip", skip.toString());
  params.append("limit", limit.toString());
  if (search) params.append("search", search);
  if (isTemplate !== undefined) params.append("is_template", isTemplate.toString());
  if (tags) params.append("tags", tags);

  const res = await fetch(`${BASE}/v1/requirements?${params}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch requirements");
  }

  return res.json();
}

export async function getRequirement(
  id: number,
  token: string
): Promise<Requirement> {
  const res = await fetch(`${BASE}/v1/requirements/${id}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch requirement");
  }

  return res.json();
}

export async function updateRequirement(
  id: number,
  data: RequirementUpdate,
  token: string
): Promise<Requirement> {
  const res = await fetch(`${BASE}/v1/requirements/${id}`, {
    method: "PUT",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to update requirement");
  }

  return res.json();
}

export async function deleteRequirement(
  id: number,
  token: string
): Promise<void> {
  const res = await fetch(`${BASE}/v1/requirements/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to delete requirement");
  }
}

export async function useRequirement(
  id: number,
  token: string
): Promise<{ id: number; title: string; description: string; usage_count: number }> {
  const res = await fetch(`${BASE}/v1/requirements/${id}/use`, {
    method: "POST",
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to use requirement");
  }

  return res.json();
}
