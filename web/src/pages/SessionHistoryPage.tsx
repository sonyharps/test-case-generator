// src/pages/SessionHistoryPage.tsx
import { useEffect, useState } from "react";
import { useAuth } from "@/store/auth.store";
import { getSessionList, getSessionDetail, type SessionSummary, type SessionDetail } from "@/api/history";
import { downloadSessionPdf, downloadSessionExcel } from "@/api/orchestrator";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Download, FileSpreadsheet, ChevronLeft, ChevronRight } from "lucide-react";
import { EditableTestCaseCard } from "@/components/test-cases/EditableTestCaseCard";
import { ApprovalControls } from "@/components/test-cases/ApprovalControls";
import { CommentsPanel } from "@/components/test-cases/CommentsPanel";

export default function SessionHistoryPage() {
  const accessToken = useAuth((state) => state.accessToken);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSession, setSelectedSession] = useState<SessionDetail | null>(null);
  const [downloadingPdf, setDownloadingPdf] = useState<string | null>(null);
  const [downloadingExcel, setDownloadingExcel] = useState<string | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [selectedTestCaseId, setSelectedTestCaseId] = useState<number | null>(null);
  const [showComments, setShowComments] = useState(false);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(5);
  const [totalSessions, setTotalSessions] = useState(0);

  useEffect(() => {
    if (accessToken) {
      loadSessions();
    } else {
      setLoading(false);
    }
  }, [accessToken, currentPage, pageSize]);

  const loadSessions = async () => {
    setLoading(true);
    setError(null);
    setSelectedSession(null); // Close detail view when changing pages
    try {
      const skip = (currentPage - 1) * pageSize;
      const response = await getSessionList(accessToken!, skip, pageSize);
      setSessions(response.sessions);
      setTotalSessions(response.total);
    } catch (err: any) {
      setError(err.message || "Failed to load sessions");
    } finally {
      setLoading(false);
    }
  };

  const viewSessionDetail = async (sessionId: string) => {
    setLoadingDetail(true);
    setError(null);
    try {
      const detail = await getSessionDetail(accessToken!, sessionId);
      console.log("Session detail received:", detail);
      console.log("First functional test case:", detail.functional[0]);
      setSelectedSession(detail);
    } catch (err: any) {
      setError(err.message || "Failed to load session detail");
    } finally {
      setLoadingDetail(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  const formatExecutionTime = (ms: number) => {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    if (minutes === 0) {
      return `${seconds}s`;
    }
    return `${minutes}m ${seconds}s`;
  };

  const handleDownloadPdf = async (sessionId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    setDownloadingPdf(sessionId);
    setError(null);

    try {
      const blob = await downloadSessionPdf(sessionId, accessToken!);
      const url = window.URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = `test_cases_${sessionId.slice(0, 8)}.pdf`;
      a.click();

      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || "Failed to download PDF");
    } finally {
      setDownloadingPdf(null);
    }
  };

  const handleDownloadExcel = async (sessionId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    setDownloadingExcel(sessionId);
    setError(null);

    try {
      const blob = await downloadSessionExcel(sessionId, accessToken!);
      const url = window.URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = `test_cases_${sessionId.slice(0, 8)}.xlsx`;
      a.click();

      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || "Failed to download Excel");
    } finally {
      setDownloadingExcel(null);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">Session History</h2>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">Session History</h2>
        <Card className="bg-red-50 border-red-200">
          <CardContent className="p-4">
            <p className="text-red-700">{error}</p>
            <Button onClick={loadSessions} className="mt-4">Retry</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Test Case Generation History</h2>
          <p className="text-gray-600 mt-1">View and manage your past test case sessions</p>
        </div>
        <Button onClick={loadSessions} variant="outline">
          Refresh
        </Button>
      </div>

      {sessions.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center text-gray-500">
            <p>No sessions found. Generate your first test cases to see them here!</p>
          </CardContent>
        </Card>
      ) : (
        <Card className="border-gray-200">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <th className="px-6 py-3">Session ID</th>
                    <th className="px-6 py-3">Requirement</th>
                    <th className="px-6 py-3">Model</th>
                    <th className="px-6 py-3">Test Cases</th>
                    <th className="px-6 py-3">Created</th>
                    <th className="px-6 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {sessions.map((session) => (
                    <tr key={session.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                        {session.session_id.slice(0, 8)}...
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 max-w-md truncate">
                        {session.requirement_text}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {session.model_used}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
                          {session.test_case_count} TCs
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {formatDate(session.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => viewSessionDetail(session.session_id)}
                            disabled={loadingDetail}
                          >
                            {loadingDetail ? "Loading..." : "View Details"}
                          </Button>
                          <Button
                            size="sm"
                            variant="default"
                            onClick={(e) => handleDownloadPdf(session.session_id, e)}
                            disabled={downloadingPdf === session.session_id}
                            className="flex items-center gap-1"
                          >
                            <Download className="w-4 h-4" />
                            {downloadingPdf === session.session_id ? "..." : "PDF"}
                          </Button>
                          <Button
                            size="sm"
                            onClick={(e) => handleDownloadExcel(session.session_id, e)}
                            disabled={downloadingExcel === session.session_id}
                            className="flex items-center gap-1 bg-emerald-600 hover:bg-emerald-700"
                          >
                            <FileSpreadsheet className="w-4 h-4" />
                            {downloadingExcel === session.session_id ? "..." : "Excel"}
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pagination Controls */}
      {!loading && sessions.length > 0 && (
        <div className="flex items-center justify-between mt-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">
              Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, totalSessions)} of {totalSessions} sessions
            </span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1); // Reset to first page when changing page size
              }}
              className="ml-4 px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={5}>5 per page</option>
              <option value={10}>10 per page</option>
              <option value={20}>20 per page</option>
              <option value={50}>50 per page</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => setCurrentPage(currentPage - 1)}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </Button>

            <div className="flex items-center gap-1">
              {Array.from({ length: Math.ceil(totalSessions / pageSize) }, (_, i) => i + 1)
                .filter((page) => {
                  // Show first page, last page, current page, and pages around current
                  const totalPages = Math.ceil(totalSessions / pageSize);
                  return (
                    page === 1 ||
                    page === totalPages ||
                    (page >= currentPage - 1 && page <= currentPage + 1)
                  );
                })
                .map((page, index, array) => {
                  // Add ellipsis if there's a gap
                  const prevPage = array[index - 1];
                  const showEllipsis = prevPage && page - prevPage > 1;

                  return (
                    <div key={page} className="flex items-center gap-1">
                      {showEllipsis && <span className="px-2 text-gray-400">...</span>}
                      <Button
                        size="sm"
                        variant={currentPage === page ? "default" : "outline"}
                        onClick={() => setCurrentPage(page)}
                        className="min-w-[40px]"
                      >
                        {page}
                      </Button>
                    </div>
                  );
                })}
            </div>

            <Button
              size="sm"
              variant="outline"
              onClick={() => setCurrentPage(currentPage + 1)}
              disabled={currentPage >= Math.ceil(totalSessions / pageSize)}
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Session Detail Modal/Panel */}
      {selectedSession && (
        <Card className="mt-6 border-indigo-200 bg-indigo-50">
          <CardContent className="p-6">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-bold text-gray-900">Session Details</h3>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={(e) => handleDownloadPdf(selectedSession.session_id, e)}
                  disabled={downloadingPdf === selectedSession.session_id}
                  className="flex items-center gap-1"
                >
                  <Download className="w-4 h-4" />
                  {downloadingPdf === selectedSession.session_id ? "Downloading..." : "PDF"}
                </Button>
                <Button
                  size="sm"
                  onClick={(e) => handleDownloadExcel(selectedSession.session_id, e)}
                  disabled={downloadingExcel === selectedSession.session_id}
                  className="flex items-center gap-1 bg-emerald-600 hover:bg-emerald-700"
                >
                  <FileSpreadsheet className="w-4 h-4" />
                  {downloadingExcel === selectedSession.session_id ? "Downloading..." : "Excel"}
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setSelectedSession(null)}>
                  Close
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
              <div>
                <span className="font-medium text-gray-700">Session ID:</span>
                <p className="text-gray-600 font-mono">{selectedSession.session_id}</p>
              </div>
              <div>
                <span className="font-medium text-gray-700">Model:</span>
                <p className="text-gray-600">{selectedSession.model_used}</p>
              </div>
              <div>
                <span className="font-medium text-gray-700">Execution Time:</span>
                <p className="text-gray-600">{formatExecutionTime(selectedSession.execution_time_ms)}</p>
              </div>
              <div>
                <span className="font-medium text-gray-700">Created:</span>
                <p className="text-gray-600">{formatDate(selectedSession.created_at)}</p>
              </div>
            </div>

            <div className="mb-4">
              <span className="font-medium text-gray-700">Requirement:</span>
              <p className="text-gray-900 mt-1 bg-white p-3 rounded border border-gray-200">
                {selectedSession.requirement_text}
              </p>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-4">
              <Card className="bg-green-50 border-green-200">
                <CardContent className="p-4 text-center">
                  <p className="text-2xl font-bold text-green-700">
                    {selectedSession.functional.length}
                  </p>
                  <p className="text-sm text-green-600">Functional</p>
                </CardContent>
              </Card>
              <Card className="bg-red-50 border-red-200">
                <CardContent className="p-4 text-center">
                  <p className="text-2xl font-bold text-red-700">
                    {selectedSession.negative.length}
                  </p>
                  <p className="text-sm text-red-600">Negative</p>
                </CardContent>
              </Card>
              <Card className="bg-yellow-50 border-yellow-200">
                <CardContent className="p-4 text-center">
                  <p className="text-2xl font-bold text-yellow-700">
                    {selectedSession.boundary.length}
                  </p>
                  <p className="text-sm text-yellow-600">Boundary</p>
                </CardContent>
              </Card>
            </div>

            <Tabs defaultValue="functional" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="functional" className="data-[state=active]:bg-green-100 data-[state=active]:text-green-700">
                  Functional ({selectedSession.functional.length})
                </TabsTrigger>
                <TabsTrigger value="negative" className="data-[state=active]:bg-red-100 data-[state=active]:text-red-700">
                  Negative ({selectedSession.negative.length})
                </TabsTrigger>
                <TabsTrigger value="boundary" className="data-[state=active]:bg-yellow-100 data-[state=active]:text-yellow-700">
                  Boundary ({selectedSession.boundary.length})
                </TabsTrigger>
              </TabsList>

              {/* Functional Test Cases Tab */}
              <TabsContent value="functional" className="space-y-4 mt-4">
                {selectedSession.functional.length === 0 ? (
                  <Card className="bg-gray-50">
                    <CardContent className="p-6 text-center text-gray-500">
                      No functional test cases generated
                    </CardContent>
                  </Card>
                ) : (
                  selectedSession.functional.map((tc: any) => (
                    <div key={tc.id || tc.tc_id} className="space-y-2">
                      <EditableTestCaseCard
                        testCase={tc}
                        onUpdate={() => viewSessionDetail(selectedSession.session_id)}
                      />
                      <div className="flex gap-2">
                        <ApprovalControls
                          testCaseId={tc.id}
                          currentStatus={tc.status || "draft"}
                          onApprovalChange={() => viewSessionDetail(selectedSession.session_id)}
                        />
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedTestCaseId(tc.id);
                            setShowComments(true);
                          }}
                        >
                          Comments
                        </Button>
                      </div>
                      {/* Show comments panel for selected test case */}
                      {showComments && selectedTestCaseId === tc.id && (
                        <div className="mt-4 border-t pt-4">
                          <CommentsPanel testCaseId={tc.id} />
                        </div>
                      )}
                    </div>
                  ))
                )}
              </TabsContent>

              {/* Negative Test Cases Tab */}
              <TabsContent value="negative" className="space-y-4 mt-4">
                {selectedSession.negative.length === 0 ? (
                  <Card className="bg-gray-50">
                    <CardContent className="p-6 text-center text-gray-500">
                      No negative test cases generated
                    </CardContent>
                  </Card>
                ) : (
                  selectedSession.negative.map((tc: any) => (
                    <div key={tc.id || tc.tc_id} className="space-y-2">
                      <EditableTestCaseCard
                        testCase={tc}
                        onUpdate={() => viewSessionDetail(selectedSession.session_id)}
                      />
                      <div className="flex gap-2">
                        <ApprovalControls
                          testCaseId={tc.id}
                          currentStatus={tc.status || "draft"}
                          onApprovalChange={() => viewSessionDetail(selectedSession.session_id)}
                        />
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedTestCaseId(tc.id);
                            setShowComments(true);
                          }}
                        >
                          Comments
                        </Button>
                      </div>
                      {/* Show comments panel for selected test case */}
                      {showComments && selectedTestCaseId === tc.id && (
                        <div className="mt-4 border-t pt-4">
                          <CommentsPanel testCaseId={tc.id} />
                        </div>
                      )}
                    </div>
                  ))
                )}
              </TabsContent>

              {/* Boundary Test Cases Tab */}
              <TabsContent value="boundary" className="space-y-4 mt-4">
                {selectedSession.boundary.length === 0 ? (
                  <Card className="bg-gray-50">
                    <CardContent className="p-6 text-center text-gray-500">
                      No boundary test cases generated
                    </CardContent>
                  </Card>
                ) : (
                  selectedSession.boundary.map((tc: any) => (
                    <div key={tc.id || tc.tc_id} className="space-y-2">
                      <EditableTestCaseCard
                        testCase={tc}
                        onUpdate={() => viewSessionDetail(selectedSession.session_id)}
                      />
                      <div className="flex gap-2">
                        <ApprovalControls
                          testCaseId={tc.id}
                          currentStatus={tc.status || "draft"}
                          onApprovalChange={() => viewSessionDetail(selectedSession.session_id)}
                        />
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedTestCaseId(tc.id);
                            setShowComments(true);
                          }}
                        >
                          Comments
                        </Button>
                      </div>
                      {/* Show comments panel for selected test case */}
                      {showComments && selectedTestCaseId === tc.id && (
                        <div className="mt-4 border-t pt-4">
                          <CommentsPanel testCaseId={tc.id} />
                        </div>
                      )}
                    </div>
                  ))
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
