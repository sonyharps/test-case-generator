// src/api/testCases.ts
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
    useAuth.getState().logout();
    window.location.href = "/login";
  }
}

// Types
export interface TestCaseEditRequest {
  title?: string;
  preconditions?: string[];
  steps?: string[];
  expected_result?: string[];
}

export interface TestCaseApprovalRequest {
  status: "draft" | "approved" | "rejected";
  rejection_reason?: string;
}

export interface CommentCreate {
  comment_text: string;
  parent_comment_id?: number;
}

export interface Comment {
  id: number;
  test_case_id: number;
  user_id: number;
  user_name: string;
  comment_text: string;
  parent_comment_id: number | null;
  is_resolved: boolean;
  created_at: string;
  replies: Comment[];
}

export interface TestCaseDetail {
  id: number;
  tc_id: string;
  title: string;
  preconditions: string[];
  steps: string[];
  expected_result: string[];
  status: "draft" | "approved" | "rejected";
  tc_type: "functional" | "negative" | "boundary";
  edit_count: number;
  edited_by: string | null;
  edited_at: string | null;
  approved_by: string | null;
  approved_at: string | null;
  rejection_reason: string | null;
  original_content: {
    title: string;
    preconditions: string[];
    steps: string[];
    expected_result: string[];
  } | null;
  created_at: string;
  updated_at: string;
}

// API Functions

export async function getTestCase(
  testCaseId: number,
  token: string
): Promise<TestCaseDetail> {
  const res = await fetch(`${BASE}/v1/test-cases/${testCaseId}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    handleAuthError(res.status);
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch test case");
  }

  return res.json();
}

export async function editTestCase(
  testCaseId: number,
  editData: TestCaseEditRequest,
  token: string
): Promise<{ message: string; test_case_id: number; edit_count: number }> {
  const res = await fetch(`${BASE}/v1/test-cases/${testCaseId}`, {
    method: "PATCH",
    headers: getAuthHeaders(token),
    body: JSON.stringify(editData),
  });

  if (!res.ok) {
    handleAuthError(res.status);
    const error = await res.json();
    throw new Error(error.detail || "Failed to edit test case");
  }

  return res.json();
}

export async function updateTestCaseApproval(
  testCaseId: number,
  approvalData: TestCaseApprovalRequest,
  token: string
): Promise<{ message: string; test_case_id: number; status: string }> {
  const res = await fetch(`${BASE}/v1/test-cases/${testCaseId}/approval`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(approvalData),
  });

  if (!res.ok) {
    handleAuthError(res.status);
    const error = await res.json();
    throw new Error(error.detail || "Failed to update approval status");
  }

  return res.json();
}

export async function addComment(
  testCaseId: number,
  commentData: CommentCreate,
  token: string
): Promise<{ message: string; comment_id: number; created_at: string }> {
  const res = await fetch(`${BASE}/v1/test-cases/${testCaseId}/comments`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(commentData),
  });

  if (!res.ok) {
    handleAuthError(res.status);
    const error = await res.json();
    throw new Error(error.detail || "Failed to add comment");
  }

  return res.json();
}

export async function getComments(
  testCaseId: number,
  token: string
): Promise<Comment[]> {
  const res = await fetch(`${BASE}/v1/test-cases/${testCaseId}/comments`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    handleAuthError(res.status);
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch comments");
  }

  return res.json();
}

export async function resolveComment(
  testCaseId: number,
  commentId: number,
  token: string
): Promise<{ message: string }> {
  const res = await fetch(
    `${BASE}/v1/test-cases/${testCaseId}/comments/${commentId}/resolve`,
    {
      method: "PATCH",
      headers: getAuthHeaders(token),
    }
  );

  if (!res.ok) {
    handleAuthError(res.status);
    const error = await res.json();
    throw new Error(error.detail || "Failed to resolve comment");
  }

  return res.json();
}
