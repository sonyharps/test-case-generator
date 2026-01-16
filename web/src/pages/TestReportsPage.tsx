// src/pages/TestReportsPage.tsx
// Test Reports & Analytics Dashboard

import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/auth.store";
import { useTestRepository } from "@/store/testRepository.store";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileText,
  Download,
} from "lucide-react";
import * as api from "@/api/testRepository";
import { TestCaseTypeLabel } from "@/lib/testRepositoryUtils";
import { toast } from "sonner";

const COLORS = {
  passed: "#22c55e",
  failed: "#ef4444",
  blocked: "#f97316",
  skipped: "#94a3b8",
  pending: "#e5e7eb",
  functional: "#3b82f6",
  negative: "#ef4444",
  boundary: "#a855f7",
  ui: "#ec4899",
  api: "#22c55e",
  integration: "#6366f1",
};

export default function TestReportsPage() {
  const token = useAuthStore((state) => state.token);
  const { projects, selectedProjectId, fetchProjects } = useTestRepository();

  // Report data states
  const [overview, setOverview] = useState<api.ProjectOverview | null>(null);
  const [passRateTrend, setPassRateTrend] = useState<api.PassRateTrendResponse | null>(null);
  const [executionSummary, setExecutionSummary] = useState<api.ExecutionSummaryResponse | null>(null);
  const [coverage, setCoverage] = useState<api.TestCaseCoverageResponse | null>(null);
  const [failingTests, setFailingTests] = useState<api.FailingTestsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [trendDays, setTrendDays] = useState(30);

  // Load projects on mount
  useEffect(() => {
    if (token) {
      fetchProjects(token);
    }
  }, [token, fetchProjects]);

  // Load reports when project selected
  useEffect(() => {
    if (selectedProjectId && token) {
      loadReports();
    } else {
      // Reset states
      setOverview(null);
      setPassRateTrend(null);
      setExecutionSummary(null);
      setCoverage(null);
      setFailingTests(null);
    }
  }, [selectedProjectId, token, trendDays]);

  const loadReports = async () => {
    if (!selectedProjectId || !token) return;

    setLoading(true);
    try {
      const [overviewData, trendData, summaryData, coverageData, failingData] =
        await Promise.all([
          api.getProjectOverview(selectedProjectId, token),
          api.getPassRateTrend(selectedProjectId, trendDays, token),
          api.getExecutionSummary(selectedProjectId, token),
          api.getTestCaseCoverage(selectedProjectId, token),
          api.getFailingTests(selectedProjectId, 10, token),
        ]);

      setOverview(overviewData);
      setPassRateTrend(trendData);
      setExecutionSummary(summaryData);
      setCoverage(coverageData);
      setFailingTests(failingData);
    } catch (error: any) {
      toast.error(error.message || "Failed to load reports");
    } finally {
      setLoading(false);
    }
  };

  const handleExportReport = async () => {
    if (!selectedProjectId || !token) return;

    try {
      const data = {
        project: overview,
        passRateTrend,
        executionSummary,
        coverage,
        failingTests,
        generatedAt: new Date().toISOString(),
      };

      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `test-report-${selectedProjectId}-${new Date().toISOString().split("T")[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success("Report exported successfully");
    } catch (error: any) {
      toast.error("Failed to export report");
    }
  };

  const selectedProject = projects.find((p) => p.id === selectedProjectId);

  // Prepare chart data
  const passRateData = passRateTrend?.data.map((d) => ({
    date: new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    passRate: d.pass_rate,
    passed: d.passed,
    failed: d.failed,
  })) || [];

  const coverageByTypeData = coverage?.coverage_by_type.map((c) => ({
    name: TestCaseTypeLabel(c.type as any),
    value: c.count,
    fill: COLORS[c.type as keyof typeof COLORS] || "#888",
  })) || [];

  const suiteCoverageData = coverage?.suite_coverage.slice(0, 10).map((c) => ({
    name: c.suite_name.length > 20 ? c.suite_name.substring(0, 20) + "..." : c.suite_name,
    cases: c.test_case_count,
    executions: c.execution_count,
  })) || [];

  const executionStatusData = executionSummary?.summaries.slice(0, 5).map((s) => ({
    name: s.run_name.length > 25 ? s.run_name.substring(0, 25) + "..." : s.run_name,
    passed: s.passed,
    failed: s.failed,
    blocked: s.blocked,
    skipped: s.skipped,
    pending: s.pending,
  })) || [];

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <FileText className="h-6 w-6 text-primary" />
            Test Reports
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Analytics and insights for your test execution
          </p>
        </div>
        {selectedProject && (
          <Button variant="outline" onClick={handleExportReport}>
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
        )}
      </div>

      {/* Project Selector */}
      <Card className="p-4">
        <Label htmlFor="project-select">Select Project</Label>
        <select
          id="project-select"
          value={selectedProjectId || ""}
          onChange={(e) => {
            const projectId = e.target.value ? parseInt(e.target.value) : null;
            // Store selection separately
            localStorage.setItem("reports-project-id", projectId?.toString() || "");
            window.location.href = `/test-repository?projectId=${projectId}`; // Navigate to set the project
          }}
          className="w-full px-3 py-2 border rounded-md text-sm bg-white mt-2"
        >
          <option value="">Select a project...</option>
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </Card>

      {!selectedProject ? (
        <Card className="p-12 text-center">
          <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-700 mb-2">
            No Project Selected
          </h3>
          <p className="text-sm text-gray-500">
            Select a project to view test reports and analytics.
          </p>
        </Card>
      ) : loading ? (
        <Card className="p-12 text-center">
          <div className="animate-pulse text-gray-400">Loading reports...</div>
        </Card>
      ) : (
        <>
          {/* Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Test Cases</p>
                  <p className="text-2xl font-bold">{overview?.total_test_cases || 0}</p>
                </div>
                <FileText className="h-8 w-8 text-blue-500" />
              </div>
            </Card>

            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Test Runs</p>
                  <p className="text-2xl font-bold">{overview?.total_test_runs || 0}</p>
                </div>
                <TrendingUp className="h-8 w-8 text-purple-500" />
              </div>
            </Card>

            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Pass Rate</p>
                  <p className="text-2xl font-bold">{overview?.overall_pass_rate || 0}%</p>
                </div>
                <div className={`h-8 w-8 rounded-full flex items-center justify-center ${
                  (overview?.overall_pass_rate || 0) >= 80 ? "bg-green-100" : (overview?.overall_pass_rate || 0) >= 50 ? "bg-yellow-100" : "bg-red-100"
                }`}>
                  {overview && overview.overall_pass_rate >= 80 ? (
                    <TrendingUp className="h-5 w-5 text-green-600" />
                  ) : (
                    <TrendingDown className="h-5 w-5 text-red-600" />
                  )}
                </div>
              </div>
            </Card>

            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Recent Activity</p>
                  <p className="text-2xl font-bold">{overview?.recent_runs_count || 0}</p>
                  <p className="text-xs text-gray-500">runs (7d)</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-orange-500" />
              </div>
            </Card>
          </div>

          {/* Pass Rate Trend */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold">Pass Rate Trend</h2>
              <select
                value={trendDays}
                onChange={(e) => setTrendDays(parseInt(e.target.value))}
                className="px-3 py-1 border rounded-md text-sm bg-white"
              >
                <option value={7}>Last 7 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
              </select>
            </div>
            {passRateData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={passRateData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" style={{ fontSize: 12 }} />
                  <YAxis domain={[0, 100]} style={{ fontSize: 12 }} />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        return (
                          <div className="bg-white border rounded-lg p-2 shadow">
                            <p className="text-sm">{payload[0].payload.date}</p>
                            <p className="text-sm font-medium">{payload[0].value}% Pass Rate</p>
                            <p className="text-xs text-gray-500">{payload[0].payload.passed} passed / {payload[0].payload.failed} failed</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="passRate" stroke={COLORS.passed} strokeWidth={2} dot={{ fill: COLORS.passed }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center py-8 text-gray-500">No data available</div>
            )}
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Execution Summary */}
            <Card className="p-6">
              <h2 className="font-semibold mb-4">Execution Summary</h2>
              {executionStatusData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={executionStatusData} layout="stacked">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" style={{ fontSize: 10 }} angle={-45} textAnchor="end" height={60} />
                    <YAxis style={{ fontSize: 12 }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="passed" stackId="status" fill={COLORS.passed} name="Passed" />
                    <Bar dataKey="failed" stackId="status" fill={COLORS.failed} name="Failed" />
                    <Bar dataKey="blocked" stackId="status" fill={COLORS.blocked} name="Blocked" />
                    <Bar dataKey="skipped" stackId="status" fill={COLORS.skipped} name="Skipped" />
                    <Bar dataKey="pending" stackId="status" fill={COLORS.pending} name="Pending" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-center py-8 text-gray-500">No test runs yet</div>
              )}
            </Card>

            {/* Coverage by Type */}
            <Card className="p-6">
              <h2 className="font-semibold mb-4">Test Cases by Type</h2>
              {coverageByTypeData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={coverageByTypeData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                    >
                      {coverageByTypeData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-center py-8 text-gray-500">No test cases yet</div>
              )}
            </Card>
          </div>

          {/* Suite Coverage */}
          <Card className="p-6">
            <h2 className="font-semibold mb-4">Suite Coverage</h2>
            {suiteCoverageData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={suiteCoverageData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" style={{ fontSize: 11 }} angle={-15} textAnchor="end" height={50} />
                  <YAxis style={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="cases" fill={COLORS.functional} name="Test Cases" />
                  <Bar dataKey="executions" fill={COLORS.passed} name="Executions" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center py-8 text-gray-500">No suites yet</div>
            )}
          </Card>

          {/* Failing Tests */}
          <Card className="p-6">
            <h2 className="font-semibold mb-4">Failing Tests (Last 30 Days)</h2>
            {failingTests?.failing_tests && failingTests.failing_tests.length > 0 ? (
              <div className="space-y-2">
                {failingTests.failing_tests.map((test) => (
                  <div key={test.test_case_id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <XCircle className="h-5 w-5 text-red-500" />
                      <div>
                        <p className="font-medium">{test.title}</p>
                        <p className="text-xs text-gray-500">Failed {test.fail_count} times</p>
                      </div>
                    </div>
                    <Badge variant="outline" className="text-red-600 border-red-200">
                      Needs Attention
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <CheckCircle2 className="h-8 w-8 text-green-500 mx-auto mb-2" />
                <p>No failing tests in the last 30 days!</p>
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
