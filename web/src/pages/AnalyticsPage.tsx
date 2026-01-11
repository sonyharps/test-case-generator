// src/pages/AnalyticsPage.tsx
import { useEffect, useState } from "react";
import { useAuth } from "@/store/auth.store";
import {
  getUserStats,
  getTimeline,
  getModelUsage,
  getTestCaseBreakdown,
  type UserStats,
  type TimelineResponse,
  type ModelUsageResponse,
  type TestCaseBreakdown,
} from "@/api/analytics";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import {
  BarChart3,
  TrendingUp,
  FileText,
  Clock,
  Cpu,
  Activity,
  Download,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

export default function AnalyticsPage() {
  const accessToken = useAuth((state) => state.accessToken);

  const [stats, setStats] = useState<UserStats | null>(null);
  const [timeline, setTimeline] = useState<TimelineResponse | null>(null);
  const [modelUsage, setModelUsage] = useState<ModelUsageResponse | null>(null);
  const [testCaseBreakdown, setTestCaseBreakdown] =
    useState<TestCaseBreakdown | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (accessToken) {
      loadAnalytics();
    }
  }, [accessToken]);

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);

    try {
      const [statsData, timelineData, modelData, breakdownData] =
        await Promise.all([
          getUserStats(accessToken!),
          getTimeline(accessToken!, 30),
          getModelUsage(accessToken!),
          getTestCaseBreakdown(accessToken!),
        ]);

      setStats(statsData);
      setTimeline(timelineData);
      setModelUsage(modelData);
      setTestCaseBreakdown(breakdownData);
    } catch (err: any) {
      setError(err.message || "Failed to load analytics");
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const exportToCSV = () => {
    if (!stats || !timeline || !modelUsage || !testCaseBreakdown) return;

    const csvData = [
      ["QA Orchestrator Analytics Export"],
      [""],
      ["Overview"],
      ["Metric", "Value"],
      ["Total Sessions", stats.total_sessions],
      ["Total Test Cases", stats.total_test_cases],
      ["Average Execution Time", formatTime(stats.avg_execution_time_ms)],
      ["Most Used Model", stats.most_used_model || "N/A"],
      [""],
      ["Test Case Breakdown"],
      ["Type", "Count"],
      ["Functional", testCaseBreakdown.functional],
      ["Negative", testCaseBreakdown.negative],
      ["Boundary", testCaseBreakdown.boundary],
      [""],
      ["Model Usage"],
      ["Model", "Sessions", "Percentage"],
      ...modelUsage.model_usage.map((m) => {
        const total = modelUsage.model_usage.reduce((sum, model) => sum + model.count, 0);
        const percentage = ((m.count / total) * 100).toFixed(1);
        return [m.model, m.count, `${percentage}%`];
      }),
      [""],
      ["Timeline (Last 30 Days)"],
      ["Date", "Sessions"],
      ...timeline.timeline.map((p) => [p.date, p.count]),
    ];

    const csvContent = csvData.map((row) => row.join(",")).join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `analytics_${new Date().toISOString().split("T")[0]}.csv`);
    link.click();
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold">Usage Analytics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold">Usage Analytics</h2>
        <Card className="bg-red-50 border-red-200">
          <CardContent className="p-4">
            <p className="text-red-700">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Usage Analytics</h2>
          <p className="text-gray-600 mt-1">
            Insights and statistics about your test case generation
          </p>
        </div>
        <Button onClick={exportToCSV} variant="outline" className="flex items-center gap-2">
          <Download className="w-4 h-4" />
          Export CSV
        </Button>
      </div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Sessions */}
        <Card className="border-blue-200 bg-gradient-to-br from-blue-50 to-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <div className="p-2 bg-blue-100 rounded-lg">
                <BarChart3 className="w-6 h-6 text-blue-600" />
              </div>
              <TrendingUp className="w-4 h-4 text-blue-500" />
            </div>
            <div className="text-3xl font-bold text-gray-900">
              {stats?.total_sessions || 0}
            </div>
            <div className="text-sm text-gray-600 mt-1">Total Sessions</div>
            <div className="text-xs text-blue-600 mt-2">
              {stats?.sessions_last_30_days || 0} in last 30 days
            </div>
          </CardContent>
        </Card>

        {/* Total Test Cases */}
        <Card className="border-green-200 bg-gradient-to-br from-green-50 to-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <div className="p-2 bg-green-100 rounded-lg">
                <FileText className="w-6 h-6 text-green-600" />
              </div>
            </div>
            <div className="text-3xl font-bold text-gray-900">
              {stats?.total_test_cases || 0}
            </div>
            <div className="text-sm text-gray-600 mt-1">Total Test Cases</div>
            <div className="text-xs text-green-600 mt-2">
              All types combined
            </div>
          </CardContent>
        </Card>

        {/* Average Execution Time */}
        <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Clock className="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <div className="text-3xl font-bold text-gray-900">
              {formatTime(stats?.avg_execution_time_ms || 0)}
            </div>
            <div className="text-sm text-gray-600 mt-1">Avg. Execution Time</div>
            <div className="text-xs text-purple-600 mt-2">Per session</div>
          </CardContent>
        </Card>

        {/* Most Used Model */}
        <Card className="border-orange-200 bg-gradient-to-br from-orange-50 to-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Cpu className="w-6 h-6 text-orange-600" />
              </div>
            </div>
            <div className="text-xl font-bold text-gray-900 truncate">
              {stats?.most_used_model || "N/A"}
            </div>
            <div className="text-sm text-gray-600 mt-1">Most Used Model</div>
            <div className="text-xs text-orange-600 mt-2">Top preference</div>
          </CardContent>
        </Card>
      </div>

      {/* Test Case Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 mb-1">Functional</div>
                <div className="text-2xl font-bold text-blue-600">
                  {testCaseBreakdown?.functional || 0}
                </div>
              </div>
              <Activity className="w-8 h-8 text-blue-500 opacity-50" />
            </div>
            <div className="mt-2 text-xs text-gray-500">
              {stats?.total_functional || 0} test cases
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-orange-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 mb-1">Negative</div>
                <div className="text-2xl font-bold text-orange-600">
                  {testCaseBreakdown?.negative || 0}
                </div>
              </div>
              <Activity className="w-8 h-8 text-orange-500 opacity-50" />
            </div>
            <div className="mt-2 text-xs text-gray-500">
              {stats?.total_negative || 0} test cases
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 mb-1">Boundary</div>
                <div className="text-2xl font-bold text-purple-600">
                  {testCaseBreakdown?.boundary || 0}
                </div>
              </div>
              <Activity className="w-8 h-8 text-purple-500 opacity-50" />
            </div>
            <div className="mt-2 text-xs text-gray-500">
              {stats?.total_boundary || 0} test cases
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Usage Pie Chart */}
        <Card>
          <CardContent className="p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Cpu className="w-5 h-5 text-gray-600" />
              Model Usage Distribution
            </h3>
            {modelUsage && modelUsage.model_usage.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={modelUsage.model_usage.map((m, idx) => ({
                      name: m.model,
                      value: m.count,
                      color: ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"][idx % 5],
                    }))}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {modelUsage.model_usage.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"][index % 5]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-gray-500">
                No model usage data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* Timeline Line Chart */}
        <Card>
          <CardContent className="p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-gray-600" />
              Activity Timeline (Last 30 Days)
            </h3>
            {timeline && timeline.timeline.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={timeline.timeline}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(date) => new Date(date).toLocaleDateString()}
                    formatter={(value) => [`${value} sessions`, "Sessions"]}
                  />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ fill: "#3b82f6", r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-gray-500">
                No activity data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
