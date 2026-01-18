// src/api/documents.ts
import { useAuth } from "@/store/auth.store";

const BASE = import.meta.env.VITE_API_BASE || "";

function getAuthHeaders(token: string): HeadersInit {
  return {
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

export interface DocumentSummary {
  id: number;
  filename: string;
  file_type: "pdf" | "docx" | "md" | "txt" | "figma" | "jira";
  title: string | null;
  content_preview: string | null;
  processing_status: "pending" | "processing" | "completed" | "failed";
  requirement_count: number;
  test_case_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentDetail {
  id: number;
  filename: string;
  file_type: string;
  file_size: number;
  title: string | null;
  full_text: string | null;
  sections: Array<{ heading: string; content: string }> | null;
  extracted_requirements: Array<{
    title: string;
    description: string;
    section: string | null;
    acceptance_criteria: string[];
    priority: string | null;
    tags: string[];
  }> | null;
  processing_status: string;
  error_message: string | null;
  chunk_count: number;
  requirement_count: number;
  test_case_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  documents: DocumentSummary[];
  total: number;
  skip: number;
  limit: number;
}

export interface DocumentUploadResponse {
  document_id: number;
  filename: string;
  file_type: string;
  file_size: number;
  processing_status: string;
  message: string;
}

export interface SimilarDocument {
  document_id: number;
  filename: string;
  title: string;
  similarity_score: number;
  content_preview: string;
}

export async function uploadDocument(
  file: File,
  token: string,
  processImmediately: boolean = true
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const url = `${BASE}/v1/documents/upload?process_immediately=${processImmediately}`;

  const res = await fetch(url, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: formData,
  });

  if (!res.ok) {
    handleAuthError(res.status);
    const error = await res.json();
    throw new Error(error.detail || "Failed to upload document");
  }

  return res.json();
}

export async function listDocuments(
  token: string,
  skip: number = 0,
  limit: number = 20,
  status?: string
): Promise<DocumentListResponse> {
  let url = `${BASE}/v1/documents?skip=${skip}&limit=${limit}`;
  if (status) {
    url += `&status=${status}`;
  }

  const res = await fetch(url, {
    method: "GET",
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    handleAuthError(res.status);
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch documents");
  }

  return res.json();
}

export async function getDocument(
  documentId: number,
  token: string
): Promise<DocumentDetail> {
  const res = await fetch(`${BASE}/v1/documents/${documentId}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    handleAuthError(res.status);
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch document");
  }

  return res.json();
}

export async function deleteDocument(
  documentId: number,
  token: string
): Promise<void> {
  const res = await fetch(`${BASE}/v1/documents/${documentId}`, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    handleAuthError(res.status);
    const error = await res.json();
    throw new Error(error.detail || "Failed to delete document");
  }
}

export async function findSimilarDocuments(
  query: string,
  token: string,
  limit: number = 5
): Promise<SimilarDocument[]> {
  const res = await fetch(
    `${BASE}/v1/documents/similar/search?query=${encodeURIComponent(query)}&limit=${limit}`,
    {
      method: "GET",
      headers: getAuthHeaders(token),
    }
  );

  if (!res.ok) {
    handleAuthError(res.status);
    const error = await res.json();
    throw new Error(error.detail || "Failed to search documents");
  }

  return res.json();
}

export async function processDocument(
  documentId: number,
  token: string,
  extractRequirements: boolean = true
): Promise<any> {
  const res = await fetch(
    `${BASE}/v1/documents/${documentId}/process?extract_requirements=${extractRequirements}`,
    {
      method: "POST",
      headers: getAuthHeaders(token),
    }
  );

  if (!res.ok) {
    handleAuthError(res.status);
    const error = await res.json();
    throw new Error(error.detail || "Failed to process document");
  }

  return res.json();
}
