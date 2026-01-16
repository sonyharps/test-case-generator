// src/api/testRepository.ts
// API client for Test Management / Repository

const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

function getAuthHeaders(token?: string | null): HeadersInit {
  const headers: HeadersInit = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

// =====================================================
// Types
// =====================================================

export enum Priority {
  CRITICAL = "critical",
  HIGH = "high",
  MEDIUM = "medium",
  LOW = "low",
}

export enum AutomationStatus {
  AUTOMATED = "automated",
  MANUAL = "manual",
  TO_BE_AUTOMATED = "to_be_automated",
  NONE = "none",
}

export enum TestCaseType {
  FUNCTIONAL = "functional",
  NEGATIVE = "negative",
  BOUNDARY = "boundary",
  UI = "ui",
  API = "api",
  INTEGRATION = "integration",
  PERFORMANCE = "performance",
  SECURITY = "security",
  USABILITY = "usability",
  OTHER = "other",
}

export interface TestStep {
  step: number;
  action: string;
  expected: string;
}

export interface Project {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by_id?: number;
  suite_count: number;
  case_count: number;
}

export interface TestSuite {
  id: number;
  name: string;
  description?: string;
  project_id: number;
  parent_id?: number;
  position: number;
  created_at: string;
  updated_at: string;
  created_by_id?: number;
  case_count: number;
  children?: TestSuite[];
  test_cases?: RepositoryTestCase[];
}

export interface RepositoryTestCase {
  id: number;
  suite_id: number;
  external_id?: string;
  title: string;
  description?: string;
  tc_type: TestCaseType;
  priority: Priority;
  automation_status: AutomationStatus;
  estimated_minutes?: number;
  preconditions?: string[];
  steps?: TestStep[];
  expected_result?: string;
  tags?: string[];
  custom_fields?: Record<string, any>;
  position: number;
  version: number;
  is_draft: boolean;
  created_at: string;
  updated_at: string;
  created_by_id?: number;
  updated_by_id?: number;
  source_session_id?: string;
  step_count: number;
}

export interface ProjectCreate {
  name: string;
  description?: string;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  is_active?: boolean;
}

export interface TestSuiteCreate {
  project_id: number;
  name: string;
  description?: string;
  parent_id?: number;
}

export interface TestSuiteUpdate {
  name?: string;
  description?: string;
  parent_id?: number;
  position?: number;
}

export interface RepositoryTestCaseCreate {
  suite_id: number;
  external_id?: string;
  title: string;
  description?: string;
  tc_type: TestCaseType;
  priority: Priority;
  automation_status: AutomationStatus;
  estimated_minutes?: number;
  preconditions?: string[];
  steps?: TestStep[];
  expected_result?: string;
  tags?: string[];
  custom_fields?: Record<string, any>;
}

export interface RepositoryTestCaseUpdate {
  title?: string;
  description?: string;
  tc_type?: TestCaseType;
  priority?: Priority;
  automation_status?: AutomationStatus;
  estimated_minutes?: number;
  tags?: string[];
  preconditions?: string[];
  steps?: TestStep[];
  expected_result?: string;
  custom_fields?: Record<string, any>;
  position?: number;
  is_draft?: boolean;
  change_summary?: string;
}

export interface SaveToRepositoryRequest {
  project_id?: number;
  project_name?: string;
  suite_id?: number;
  suite_name?: string;
  test_cases: Omit<RepositoryTestCaseCreate, "suite_id">[];
  source_session_id?: string;
}

export interface TestCasesListParams {
  project_id?: number;
  suite_id?: number;
  tc_type?: TestCaseType;
  priority?: Priority;
  automation_status?: AutomationStatus;
  is_draft?: boolean;
  search?: string;
  tags?: string;
  page?: number;
  page_size?: number;
}

export interface TestCasesListResponse {
  test_cases: RepositoryTestCase[];
  total: number;
  page: number;
  page_size: number;
}

// =====================================================
// Projects API
// =====================================================

export async function listProjects(token: string): Promise<{ projects: Project[]; total: number }> {
  const res = await fetch(`${BASE}/v1/test-repository/projects`, {
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to list projects: ${res.statusText}`);
  return res.json();
}

export async function getProject(projectId: number, token: string): Promise<Project> {
  const res = await fetch(`${BASE}/v1/test-repository/projects/${projectId}`, {
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to get project: ${res.statusText}`);
  return res.json();
}

export async function createProject(data: ProjectCreate, token: string): Promise<Project> {
  const res = await fetch(`${BASE}/v1/test-repository/projects`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to create project: ${res.statusText}`);
  return res.json();
}

export async function updateProject(projectId: number, data: ProjectUpdate, token: string): Promise<Project> {
  const res = await fetch(`${BASE}/v1/test-repository/projects/${projectId}`, {
    method: "PUT",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to update project: ${res.statusText}`);
  return res.json();
}

export async function deleteProject(projectId: number, token: string): Promise<void> {
  const res = await fetch(`${BASE}/v1/test-repository/projects/${projectId}`, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to delete project: ${res.statusText}`);
}

// =====================================================
// Test Suites API
// =====================================================

export async function listSuites(params: { project_id?: number; parent_id?: number }, token: string): Promise<{ suites: TestSuite[]; total: number }> {
  const queryParams = new URLSearchParams();
  if (params.project_id) queryParams.append("project_id", params.project_id.toString());
  if (params.parent_id !== undefined) {
    if (params.parent_id === null) {
      queryParams.append("parent_id", "null");
    } else {
      queryParams.append("parent_id", params.parent_id.toString());
    }
  }

  const res = await fetch(`${BASE}/v1/test-repository/suites?${queryParams}`, {
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to list suites: ${res.statusText}`);
  return res.json();
}

export async function getSuite(suiteId: number, token: string): Promise<TestSuite> {
  const res = await fetch(`${BASE}/v1/test-repository/suites/${suiteId}`, {
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to get suite: ${res.statusText}`);
  return res.json();
}

export async function createSuite(data: TestSuiteCreate, token: string): Promise<TestSuite> {
  const res = await fetch(`${BASE}/v1/test-repository/suites`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to create suite: ${res.statusText}`);
  return res.json();
}

export async function updateSuite(suiteId: number, data: TestSuiteUpdate, token: string): Promise<TestSuite> {
  const res = await fetch(`${BASE}/v1/test-repository/suites/${suiteId}`, {
    method: "PUT",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to update suite: ${res.statusText}`);
  return res.json();
}

export async function deleteSuite(suiteId: number, token: string): Promise<void> {
  const res = await fetch(`${BASE}/v1/test-repository/suites/${suiteId}`, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to delete suite: ${res.statusText}`);
  }
}

// =====================================================
// Repository Test Cases API
// =====================================================

export async function listTestCases(params: TestCasesListParams, token: string): Promise<TestCasesListResponse> {
  const queryParams = new URLSearchParams();
  if (params.project_id) queryParams.append("project_id", params.project_id.toString());
  if (params.suite_id) queryParams.append("suite_id", params.suite_id.toString());
  if (params.tc_type) queryParams.append("tc_type", params.tc_type);
  if (params.priority) queryParams.append("priority", params.priority);
  if (params.automation_status) queryParams.append("automation_status", params.automation_status);
  if (params.is_draft !== undefined) queryParams.append("is_draft", params.is_draft.toString());
  if (params.search) queryParams.append("search", params.search);
  if (params.tags) queryParams.append("tags", params.tags);
  queryParams.append("page", (params.page || 1).toString());
  queryParams.append("page_size", (params.page_size || 20).toString());

  const res = await fetch(`${BASE}/v1/test-repository/test-cases?${queryParams}`, {
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to list test cases: ${res.statusText}`);
  return res.json();
}

export async function getTestCase(testCaseId: number, token: string): Promise<RepositoryTestCase> {
  const res = await fetch(`${BASE}/v1/test-repository/test-cases/${testCaseId}`, {
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to get test case: ${res.statusText}`);
  return res.json();
}

export async function createTestCase(data: RepositoryTestCaseCreate, token: string): Promise<RepositoryTestCase> {
  const res = await fetch(`${BASE}/v1/test-repository/test-cases`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to create test case: ${res.statusText}`);
  return res.json();
}

export async function updateTestCase(testCaseId: number, data: RepositoryTestCaseUpdate, token: string): Promise<RepositoryTestCase> {
  const res = await fetch(`${BASE}/v1/test-repository/test-cases/${testCaseId}`, {
    method: "PUT",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to update test case: ${res.statusText}`);
  return res.json();
}

export async function deleteTestCase(testCaseId: number, token: string): Promise<void> {
  const res = await fetch(`${BASE}/v1/test-repository/test-cases/${testCaseId}`, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to delete test case: ${res.statusText}`);
}

export async function bulkUpdateTestCases(testCaseIds: number[], updates: RepositoryTestCaseUpdate, token: string): Promise<{ updated_count: number; updated_ids: number[] }> {
  const res = await fetch(`${BASE}/v1/test-repository/test-cases/bulk`, {
    method: "PUT",
    headers: getAuthHeaders(token),
    body: JSON.stringify({ test_case_ids: testCaseIds, updates }),
  });
  if (!res.ok) throw new Error(`Failed to bulk update test cases: ${res.statusText}`);
  return res.json();
}

export async function bulkDeleteTestCases(testCaseIds: number[], token: string): Promise<{ deleted_count: number; deleted_ids: number[] }> {
  const res = await fetch(`${BASE}/v1/test-repository/test-cases/bulk`, {
    method: "DELETE",
    headers: getAuthHeaders(token),
    body: JSON.stringify(testCaseIds),
  });
  if (!res.ok) throw new Error(`Failed to bulk delete test cases: ${res.statusText}`);
  return res.json();
}

// =====================================================
// Save from Orchestrator
// =====================================================

export async function saveFromOrchestrator(data: SaveToRepositoryRequest, token: string): Promise<{ project_id: number; suite_id: number; created_count: number; test_case_ids: number[] }> {
  const res = await fetch(`${BASE}/v1/test-repository/save-from-orchestrator`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Failed to save to repository: ${res.status} ${txt}`);
  }
  return res.json();
}

// =====================================================
// Import / Export
// =====================================================

export async function exportTestCases(params: { project_id?: number; suite_id?: number; format: "json" | "csv" }, token: string): Promise<any> {
  const res = await fetch(`${BASE}/v1/test-repository/test-cases/export`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`Failed to export test cases: ${res.statusText}`);
  return res.json();
}

export async function importTestCases(suiteId: number, testCases: RepositoryTestCaseCreate[], overwrite: boolean, token: string): Promise<{ imported_count: number; updated_count: number; failed_count: number; errors: string[] }> {
  const res = await fetch(`${BASE}/v1/test-repository/test-cases/import`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      suite_id: suiteId,
      test_cases: testCases.map(tc => ({ ...tc, suite_id: suiteId })),
      overwrite,
    }),
  });
  if (!res.ok) throw new Error(`Failed to import test cases: ${res.statusText}`);
  return res.json();
}

// =====================================================
// Test Runs API
// =====================================================

export enum TestRunStatus {
  PLANNED = "planned",
  IN_PROGRESS = "in_progress",
  COMPLETED = "completed",
  CANCELLED = "cancelled",
}

export enum TestResultStatus {
  PASSED = "passed",
  FAILED = "failed",
  BLOCKED = "blocked",
  SKIPPED = "skipped",
  RETEST = "retest",
  PENDING = "pending",
}

export interface EvidenceItem {
  id: string;
  type: "image" | "video";
  url: string;
  thumbnail_url?: string;
  filename: string;
  size_bytes: number;
  uploaded_at: string;
}

export interface Milestone {
  id: number;
  name: string;
  description?: string;
  project_id: number;
  due_date?: string;
  is_completed: boolean;
  created_at: string;
  updated_at: string;
}

export interface MilestoneCreate {
  project_id: number;
  name: string;
  description?: string;
  due_date?: string;
}

export interface TestRun {
  id: number;
  name: string;
  description?: string;
  project_id: number;
  milestone_id?: number;
  status: TestRunStatus;
  include_all: boolean;
  included_case_ids?: number[];
  created_at: string;
  updated_at: string;
  created_by_id?: number;
  completed_at?: string;
  progress: {
    total: number;
    passed: number;
    failed: number;
    blocked: number;
    skipped: number;
    pending: number;
    pass_rate: number;
  };
}

export interface TestRunWithResults extends TestRun {
  test_results: TestResult[];
}

export interface TestResult {
  id: number;
  test_run_id: number;
  test_case_id: number;
  status: TestResultStatus;
  assigned_to_id?: number;
  actual_result?: string;
  comments?: string;
  defects?: string[];
  execution_seconds?: number;
  executed_at?: string;
  executed_by_id?: number;
  created_at: string;
  updated_at: string;
  evidence?: EvidenceItem[];
  test_case?: RepositoryTestCase;
}

export interface TestRunCreate {
  project_id: number;
  name: string;
  description?: string;
  milestone_id?: number;
  include_all?: boolean;
  included_case_ids?: number[];
}

export interface TestResultUpdate {
  status?: TestResultStatus;
  actual_result?: string;
  comments?: string;
  defects?: string[];
  execution_seconds?: number;
}

// =====================================================
// Milestones API
// =====================================================

export async function listMilestones(projectId: number, token: string): Promise<{ milestones: Milestone[]; total: number }> {
  const res = await fetch(`${BASE}/v1/test-repository/milestones?project_id=${projectId}`, {
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to list milestones: ${res.statusText}`);
  return res.json();
}

export async function createMilestone(data: MilestoneCreate, token: string): Promise<Milestone> {
  const res = await fetch(`${BASE}/v1/test-repository/milestones`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to create milestone: ${res.statusText}`);
  return res.json();
}

// =====================================================
// Test Runs API
// =====================================================

export async function listTestRuns(params: { project_id: number; status?: TestRunStatus; milestone_id?: number }, token: string): Promise<{ test_runs: TestRun[]; total: number }> {
  const queryParams = new URLSearchParams();
  queryParams.append("project_id", params.project_id.toString());
  if (params.status) queryParams.append("status", params.status);
  if (params.milestone_id) queryParams.append("milestone_id", params.milestone_id.toString());

  const res = await fetch(`${BASE}/v1/test-repository/test-runs?${queryParams}`, {
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to list test runs: ${res.statusText}`);
  return res.json();
}

export async function getTestRun(testRunId: number, token: string): Promise<TestRunWithResults> {
  const res = await fetch(`${BASE}/v1/test-repository/test-runs/${testRunId}`, {
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to get test run: ${res.statusText}`);
  return res.json();
}

export async function createTestRun(data: TestRunCreate, token: string): Promise<TestRun> {
  const res = await fetch(`${BASE}/v1/test-repository/test-runs`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Failed to create test run: ${res.status} ${txt}`);
  }
  return res.json();
}

export async function updateTestRun(testRunId: number, data: { status?: TestRunStatus; name?: string; description?: string }, token: string): Promise<TestRun> {
  const res = await fetch(`${BASE}/v1/test-repository/test-runs/${testRunId}`, {
    method: "PUT",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || `Failed to update test run: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteTestRun(testRunId: number, token: string): Promise<void> {
  const res = await fetch(`${BASE}/v1/test-repository/test-runs/${testRunId}`, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to delete test run: ${res.statusText}`);
  }
}

export async function cancelTestRun(testRunId: number, token: string): Promise<TestRun> {
  const res = await fetch(`${BASE}/v1/test-repository/test-runs/${testRunId}/cancel`, {
    method: "POST",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to cancel test run: ${res.statusText}`);
  }
  return res.json();
}

// =====================================================
// Test Results API
// =====================================================

export async function updateTestResult(resultId: number, data: TestResultUpdate, token: string): Promise<TestResult> {
  const res = await fetch(`${BASE}/v1/test-repository/test-results/${resultId}`, {
    method: "PUT",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to update test result: ${res.statusText}`);
  return res.json();
}

export async function bulkUpdateTestResults(resultIds: number[], data: { status?: TestResultStatus; assigned_to_id?: number }, token: string): Promise<{ updated_count: number; updated_ids: number[] }> {
  const res = await fetch(`${BASE}/v1/test-repository/test-results/bulk`, {
    method: "PUT",
    headers: getAuthHeaders(token),
    body: JSON.stringify({ result_ids: resultIds, ...data }),
  });
  if (!res.ok) throw new Error(`Failed to bulk update test results: ${res.statusText}`);
  return res.json();
}

// =====================================================
// Evidence Upload API
// =====================================================

export async function uploadEvidence(resultId: number, file: File, token: string): Promise<EvidenceItem> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${BASE}/v1/test-repository/test-results/${resultId}/evidence`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
    },
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || `Failed to upload evidence: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteEvidence(resultId: number, evidenceId: string, token: string): Promise<void> {
  const res = await fetch(`${BASE}/v1/test-repository/test-results/${resultId}/evidence/${evidenceId}`, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to delete evidence: ${res.statusText}`);
}

export function getEvidenceUrl(evidenceId: string, token?: string): string {
  const url = `${BASE}/v1/test-repository/evidence/${evidenceId}`;
  if (token) {
    return `${url}?token=${token}`;
  }
  return url;
}

// =====================================================
// Reports API
// =====================================================

export interface ProjectOverview {
  project_id: number;
  project_name: string;
  total_test_cases: number;
  total_test_runs: number;
  overall_pass_rate: number;
  test_cases_by_type: Record<string, number>;
  recent_runs_count: number;
}

export interface PassRateTrendData {
  date: string;
  runs: number;
  total_tests: number;
  passed: number;
  failed: number;
  pass_rate: number;
}

export interface PassRateTrendResponse {
  project_id: number;
  period_days: number;
  data: PassRateTrendData[];
}

export interface ExecutionSummary {
  run_id: number;
  run_name: string;
  status: TestRunStatus;
  created_at: string;
  completed_at: string | null;
  total: number;
  passed: number;
  failed: number;
  blocked: number;
  skipped: number;
  pending: number;
  pass_rate: number;
}

export interface ExecutionSummaryResponse {
  project_id: number;
  summaries: ExecutionSummary[];
  total: number;
}

export interface TestCaseCoverage {
  suite_id: number;
  suite_name: string;
  test_case_count: number;
  execution_count: number;
}

export interface CoverageByType {
  type: string;
  count: number;
}

export interface TestCaseCoverageResponse {
  project_id: number;
  suite_coverage: TestCaseCoverage[];
  coverage_by_type: CoverageByType[];
}

export interface FailingTest {
  test_case_id: number;
  title: string;
  suite_id: number;
  fail_count: number;
}

export interface FailingTestsResponse {
  project_id: number;
  period_days: number;
  failing_tests: FailingTest[];
}

export async function getProjectOverview(projectId: number, token: string): Promise<ProjectOverview> {
  const res = await fetch(`${BASE}/v1/test-repository/reports/overview?project_id=${projectId}`, {
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to get project overview: ${res.statusText}`);
  return res.json();
}

export async function getPassRateTrend(projectId: number, days: number = 30, token: string): Promise<PassRateTrendResponse> {
  const res = await fetch(`${BASE}/v1/test-repository/reports/pass-rate-trend?project_id=${projectId}&days=${days}`, {
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to get pass rate trend: ${res.statusText}`);
  return res.json();
}

export async function getExecutionSummary(projectId: number, token: string, status?: TestRunStatus): Promise<ExecutionSummaryResponse> {
  const params = new URLSearchParams();
  params.append("project_id", projectId.toString());
  if (status) params.append("status", status);

  const res = await fetch(`${BASE}/v1/test-repository/reports/execution-summary?${params}`, {
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to get execution summary: ${res.statusText}`);
  return res.json();
}

export async function getTestCaseCoverage(projectId: number, token: string): Promise<TestCaseCoverageResponse> {
  const res = await fetch(`${BASE}/v1/test-repository/reports/test-case-coverage?project_id=${projectId}`, {
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to get test case coverage: ${res.statusText}`);
  return res.json();
}

export async function getFailingTests(projectId: number, limit: number = 20, token: string): Promise<FailingTestsResponse> {
  const res = await fetch(`${BASE}/v1/test-repository/reports/failing-tests?project_id=${projectId}&limit=${limit}`, {
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to get failing tests: ${res.statusText}`);
  return res.json();
}

export async function exportTestRunReport(testRunId: number, token: string): Promise<any> {
  const res = await fetch(`${BASE}/v1/test-repository/reports/run/${testRunId}/export`, {
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to export test run: ${res.statusText}`);
  return res.json();
}

// =====================================================
// Version Control API
// =====================================================

export interface TestCaseVersion {
  id: number;
  test_case_id: number;
  version: number;
  title: string;
  description?: string;
  tc_type: TestCaseType;
  priority: Priority;
  automation_status: AutomationStatus;
  estimated_minutes?: number;
  preconditions?: string[];
  steps?: TestStep[];
  expected_result?: string;
  tags?: string[];
  custom_fields?: Record<string, unknown>;
  change_summary?: string;
  changed_by_id?: number;
  created_at: string;
  updated_at: string;
}

export interface TestCaseVersionListResponse {
  versions: TestCaseVersion[];
  total: number;
}

export async function getTestCaseVersions(testCaseId: number, token: string): Promise<TestCaseVersionListResponse> {
  const res = await fetch(`${BASE}/v1/test-repository/test-cases/${testCaseId}/versions`, {
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to get test case versions: ${res.statusText}`);
  return res.json();
}

export async function restoreTestCaseVersion(
  testCaseId: number,
  versionId: number,
  changeSummary?: string,
  token: string
): Promise<RepositoryTestCase> {
  const res = await fetch(`${BASE}/v1/test-repository/test-cases/${testCaseId}/versions/${versionId}/restore`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify({ change_summary: changeSummary }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to restore version: ${res.statusText}`);
  }
  return res.json();
}

// Re-exports to ensure types are available
export type { EvidenceItem };
