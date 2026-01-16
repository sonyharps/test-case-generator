// src/pages/LandingPage.tsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/store/auth.store";
import { getDashboardStats, getRepositoryStats, type DashboardStats, type RepositoryStats } from "@/api/dashboard";
import { getSessionList, type SessionSummary } from "@/api/history";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  Activity,
  FileText,
  Clock,
  TrendingUp,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Eye,
  FolderOpen,
  Folder,
  Save
} from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";

export default function LandingPage() {
  const navigate = useNavigate();
  const { accessToken, user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [repoStats, setRepoStats] = useState<RepositoryStats | null>(null);
  const [recentSessions, setRecentSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (accessToken) {
      loadDashboardData();
    } else {
      setLoading(false);
    }
  }, [accessToken]);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Load stats, repository stats, and recent sessions in parallel
      const [statsData, repoData, sessionsData] = await Promise.all([
        getDashboardStats(accessToken!),
        getRepositoryStats(accessToken!),
        getSessionList(accessToken!, 0, 5)
      ]);
      setStats(statsData);
      setRepoStats(repoData);
      setRecentSessions(sessionsData.sessions);
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  const formatExecutionTime = (ms: number) => {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    if (minutes === 0) return `${seconds}s`;
    return `${minutes}m ${seconds}s`;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!accessToken) {
    // Not logged in - show marketing page
    return (
      <div className="space-y-8">
        <section className="text-center space-y-4 py-12">
          <h1 className="text-4xl font-bold text-gray-900">
            Welcome to QA Orchestrator
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            AI-powered test case generation for enterprise teams
          </p>
          <div className="flex gap-3 justify-center pt-4">
            <Button onClick={() => navigate("/login")} size="lg">
              Login
            </Button>
            <Button onClick={() => navigate("/register")} variant="outline" size="lg">
              Register
            </Button>
          </div>
        </section>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid gap-4 md:grid-cols-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">Dashboard</h2>
        <Card className="bg-red-50 border-red-200">
          <CardContent className="p-6">
            <p className="text-red-700">{error}</p>
            <Button onClick={loadDashboardData} className="mt-4">Retry</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  // Prepare chart data
  const distributionData = [
    { name: "Functional", value: stats.test_case_distribution.functional, color: "#3b82f6" },
    { name: "Negative", value: stats.test_case_distribution.negative, color: "#ef4444" },
    { name: "Boundary", value: stats.test_case_distribution.boundary, color: "#f59e0b" },
  ].filter(item => item.value > 0);

  const approvalData = [
    { name: "Draft", value: stats.approval_stats.draft, color: "#94a3b8" },
    { name: "Approved", value: stats.approval_stats.approved, color: "#10b981" },
    { name: "Rejected", value: stats.approval_stats.rejected, color: "#ef4444" },
  ].filter(item => item.value > 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.username || "User"}! 👋
          </h1>
          <p className="text-gray-600 mt-1">Here's what's happening with your test cases</p>
        </div>
        <Button onClick={() => navigate("/orchestrator")} size="lg" className="bg-blue-600 hover:bg-blue-700">
          <Activity className="w-4 h-4 mr-2" />
          Generate Test Cases
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Sessions</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-2">{stats.total_sessions}</h3>
              </div>
              <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center">
                <FileText className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Test Cases</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-2">{stats.total_test_cases}</h3>
              </div>
              <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircle2 className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg. Time</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-2">
                  {formatExecutionTime(stats.avg_execution_time_ms)}
                </h3>
              </div>
              <div className="h-12 w-12 bg-purple-100 rounded-full flex items-center justify-center">
                <Clock className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Last Generated</p>
                <h3 className="text-sm font-semibold text-gray-900 mt-2">
                  {stats.last_generation_date
                    ? formatDate(stats.last_generation_date)
                    : "No sessions yet"}
                </h3>
              </div>
              <div className="h-12 w-12 bg-orange-100 rounded-full flex items-center justify-center">
                <TrendingUp className="h-6 w-6 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Repository Stats */}
      {repoStats && (repoStats.total_projects > 0 || repoStats.total_test_cases > 0) && (
        <Card className="bg-indigo-50 border-indigo-200">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="text-lg font-semibold flex items-center gap-2">
                <FolderOpen className="h-5 w-5 text-indigo-600" />
                Test Repository
              </CardTitle>
              <Button variant="outline" size="sm" onClick={() => navigate("/test-repository")}>
                View Repository
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 bg-indigo-100 rounded-full flex items-center justify-center">
                  <Folder className="h-5 w-5 text-indigo-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Projects</p>
                  <h4 className="text-xl font-bold text-gray-900">{repoStats.total_projects}</h4>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 bg-indigo-100 rounded-full flex items-center justify-center">
                  <FolderOpen className="h-5 w-5 text-indigo-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Suites</p>
                  <h4 className="text-xl font-bold text-gray-900">{repoStats.total_suites}</h4>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 bg-green-100 rounded-full flex items-center justify-center">
                  <CheckCircle2 className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Saved Test Cases</p>
                  <h4 className="text-xl font-bold text-gray-900">{repoStats.total_test_cases}</h4>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 bg-purple-100 rounded-full flex items-center justify-center">
                  <Save className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Saved This Month</p>
                  <h4 className="text-xl font-bold text-gray-900">{repoStats.saved_this_month}</h4>
                </div>
              </div>
            </div>
            {stats.total_test_cases > 0 && (
              <div className="mt-4 pt-4 border-t border-indigo-200">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <span>Save Rate:</span>
                  <Badge variant="secondary" className="bg-indigo-100 text-indigo-700">
                    {Math.round((repoStats.total_test_cases / stats.total_test_cases) * 100)}%
                  </Badge>
                  <span>({repoStats.total_test_cases} of {stats.total_test_cases} test cases saved)</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Charts Row */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Test Case Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Test Case Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {distributionData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={distributionData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {distributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
                No test cases generated yet
              </div>
            )}
          </CardContent>
        </Card>

        {/* Approval Status */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Approval Status</CardTitle>
          </CardHeader>
          <CardContent>
            {approvalData.length > 0 ? (
              <>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={approvalData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={70}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {approvalData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="grid grid-cols-3 gap-4 mt-4">
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-2">
                      <AlertCircle className="h-4 w-4 text-gray-500" />
                      <span className="text-sm text-gray-600">Draft</span>
                    </div>
                    <p className="text-xl font-bold text-gray-900 mt-1">{stats.approval_stats.draft}</p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      <span className="text-sm text-gray-600">Approved</span>
                    </div>
                    <p className="text-xl font-bold text-green-600 mt-1">{stats.approval_stats.approved}</p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-2">
                      <XCircle className="h-4 w-4 text-red-600" />
                      <span className="text-sm text-gray-600">Rejected</span>
                    </div>
                    <p className="text-xl font-bold text-red-600 mt-1">{stats.approval_stats.rejected}</p>
                  </div>
                </div>
              </>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
                No test cases generated yet
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Sessions */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="text-lg font-semibold">Recent Sessions</CardTitle>
            <Button variant="outline" size="sm" onClick={() => navigate("/history")}>
              View All
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {recentSessions.length > 0 ? (
            <div className="space-y-3">
              {recentSessions.map((session) => (
                <div
                  key={session.id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex-1">
                    <p className="font-medium text-gray-900 truncate max-w-md">
                      {session.requirement_text}
                    </p>
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                      <span className="flex items-center gap-1">
                        <FileText className="h-3 w-3" />
                        {session.test_case_count} test cases
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatExecutionTime(session.execution_time_ms)}
                      </span>
                      <span>{formatDate(session.created_at)}</span>
                    </div>
                  </div>
                  <div className="flex gap-2 ml-4">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => navigate("/history")}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <FileText className="h-12 w-12 mx-auto text-gray-400 mb-3" />
              <p className="font-medium">No sessions yet</p>
              <p className="text-sm mt-1">Generate your first test cases to get started</p>
              <Button onClick={() => navigate("/orchestrator")} className="mt-4">
                Generate Test Cases
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
