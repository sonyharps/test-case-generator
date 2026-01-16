// src/pages/TestRunsPage.tsx
// Test Runs & Execution Page - Execute test cases and record results

import { useEffect, useState, useRef } from "react";
import { useAuthStore } from "@/store/auth.store";
import { useTestRuns } from "@/store/testRuns.store";
import { useTestRepository } from "@/store/testRepository.store";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Play,
  Plus,
  CheckCircle2,
  XCircle,
  AlertCircle,
  SkipForward,
  Clock,
  Flag,
  ListTodo,
  Edit,
  Trash2,
  Image as ImageIcon,
  Video,
  Upload,
  X,
  Ban,
  MoreVertical,
} from "lucide-react";
import { TestRunStatus, TestResultStatus, uploadEvidence, deleteEvidence, getEvidenceUrl } from "@/api/testRepository";
import type { EvidenceItem } from "@/api/testRepository";
import { toast } from "sonner";

export default function TestRunsPage() {
  const token = useAuthStore((state) => state.token);

  const {
    // State
    testRuns,
    selectedTestRunId,
    selectedTestRun,
    testRunsLoading,
    isCreatingRun,
    isExecutingRun,
    milestones,

    // Actions
    fetchTestRuns,
    fetchTestRun,
    createTestRun,
    updateTestRun,
    deleteTestRun,
    cancelTestRun,
    selectTestRun,
    setCreatingRun,
    setExecutingRun,
    fetchMilestones,
    createMilestone,
    updateTestResult,
    bulkUpdateResults,
  } = useTestRuns();

  const { projects, selectedProjectId, fetchProjects } = useTestRepository();

  // Form states
  const [runForm, setRunForm] = useState({
    name: "",
    description: "",
    milestone_id: undefined as number | undefined,
  });

  // Result editing state
  const [editingResultId, setEditingResultId] = useState<number | null>(null);
  const [resultForm, setResultForm] = useState({
    status: TestResultStatus.PENDING,
    comments: "",
    actual_result: "",
  });
  const [uploadingEvidence, setUploadingEvidence] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load projects on mount
  useEffect(() => {
    if (token) {
      fetchProjects(token);
    }
  }, [token, fetchProjects]);

  // Load test runs when project selected
  useEffect(() => {
    if (selectedProjectId && token) {
      fetchTestRuns(selectedProjectId, token);
      fetchMilestones(selectedProjectId, token);
    }
  }, [selectedProjectId, token, fetchTestRuns, fetchMilestones]);

  // Load selected test run details
  useEffect(() => {
    if (selectedTestRunId && token) {
      fetchTestRun(selectedTestRunId, token);
    }
  }, [selectedTestRunId, token, fetchTestRun]);

  // Handlers
  const handleCreateRun = async () => {
    if (!token || !selectedProjectId) return;

    await createTestRun(
      {
        project_id: selectedProjectId,
        name: runForm.name,
        description: runForm.description,
        milestone_id: runForm.milestone_id,
        include_all: true, // For now, include all test cases
      },
      token
    );

    setRunForm({ name: "", description: "", milestone_id: undefined });
    setCreatingRun(false);
    toast.success("Test run created successfully");
  };

  const handleStartRun = async () => {
    if (!selectedTestRunId || !token) return;

    await updateTestRun(selectedTestRunId, { status: TestRunStatus.IN_PROGRESS }, token);
    toast.success("Test run started");
  };

  const handleCompleteRun = async () => {
    if (!selectedTestRunId || !token) return;

    try {
      await updateTestRun(selectedTestRunId, { status: TestRunStatus.COMPLETED }, token);
      toast.success("Test run completed");
    } catch (error: any) {
      toast.error(error.message || "Failed to complete test run");
    }
  };

  const handleCancelRun = async () => {
    if (!selectedTestRunId || !token) return;

    if (!confirm("Are you sure you want to cancel this test run?")) return;

    try {
      await cancelTestRun(selectedTestRunId, token);
      toast.success("Test run cancelled");
      // Refresh the test run to get updated status
      await fetchTestRun(selectedTestRunId, token);
    } catch (error: any) {
      toast.error(error.message || "Failed to cancel test run");
    }
  };

  const handleDeleteRun = async () => {
    if (!selectedTestRunId || !token) return;

    if (!confirm("Are you sure you want to delete this test run? This action cannot be undone.")) return;

    try {
      await deleteTestRun(selectedTestRunId, token);
      toast.success("Test run deleted");
      selectTestRun(null);
    } catch (error: any) {
      toast.error(error.message || "Failed to delete test run");
    }
  };

  const handleDeleteRunWithId = async (testRunId: number) => {
    if (!token) return;

    if (!confirm("Are you sure you want to delete this test run? This action cannot be undone.")) return;

    try {
      await deleteTestRun(testRunId, token);
      toast.success("Test run deleted");
      if (selectedTestRunId === testRunId) {
        selectTestRun(null);
      }
    } catch (error: any) {
      toast.error(error.message || "Failed to delete test run");
    }
  };

  const handleUpdateResult = async (resultId: number, data: { status: TestResultStatus; comments?: string; actual_result?: string }) => {
    if (!token) return;

    await updateTestResult(resultId, data, token);
    setEditingResultId(null);
    setResultForm({ status: TestResultStatus.PENDING, comments: "", actual_result: "" });
  };

  const handleQuickStatusUpdate = async (resultIds: number[], status: TestResultStatus) => {
    if (!token) return;

    if (resultIds.length === 0) {
      toast.error("No test results found to update");
      return;
    }

    try {
      await bulkUpdateResults(resultIds, { status }, token);
      toast.success(`Marked ${resultIds.length} test(s) as ${status}`);
    } catch (error: any) {
      toast.error(error.message || "Failed to update test results");
    }
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !editingResultId || !token) return;

    // Validate file type
    const allowedImageTypes = ["image/jpeg", "image/png", "image/gif", "image/webp"];
    const allowedVideoTypes = ["video/mp4", "video/webm", "video/quicktime", "video/x-msvideo"];
    if (![...allowedImageTypes, ...allowedVideoTypes].includes(file.type)) {
      toast.error("Invalid file type. Please upload an image or video.");
      return;
    }

    // Validate file size (20MB)
    if (file.size > 20 * 1024 * 1024) {
      toast.error("File too large. Maximum size is 20MB.");
      return;
    }

    setUploadingEvidence(true);
    try {
      const evidence = await uploadEvidence(editingResultId, file, token);
      toast.success("Evidence uploaded successfully");
      // Refresh the test run to get updated evidence
      await fetchTestRun(selectedTestRunId!, token);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (error: any) {
      toast.error(error.message || "Failed to upload evidence");
    } finally {
      setUploadingEvidence(false);
    }
  };

  const handleDeleteEvidence = async (resultId: number, evidenceId: string) => {
    if (!token) return;

    try {
      await deleteEvidence(resultId, evidenceId, token);
      toast.success("Evidence deleted");
      // Refresh the test run
      await fetchTestRun(selectedTestRunId!, token);
    } catch (error: any) {
      toast.error(error.message || "Failed to delete evidence");
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  const getStatusIcon = (status: TestResultStatus) => {
    switch (status) {
      case TestResultStatus.PASSED:
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case TestResultStatus.FAILED:
        return <XCircle className="h-4 w-4 text-red-600" />;
      case TestResultStatus.BLOCKED:
        return <AlertCircle className="h-4 w-4 text-orange-600" />;
      case TestResultStatus.SKIPPED:
        return <SkipForward className="h-4 w-4 text-gray-400" />;
      case TestResultStatus.RETEST:
        return <Clock className="h-4 w-4 text-yellow-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-300" />;
    }
  };

  const getStatusColor = (status: TestResultStatus) => {
    switch (status) {
      case TestResultStatus.PASSED:
        return "bg-green-100 text-green-700 border-green-200";
      case TestResultStatus.FAILED:
        return "bg-red-100 text-red-700 border-red-200";
      case TestResultStatus.BLOCKED:
        return "bg-orange-100 text-orange-700 border-orange-200";
      case TestResultStatus.SKIPPED:
        return "bg-gray-100 text-gray-500 border-gray-200";
      case TestResultStatus.RETEST:
        return "bg-yellow-100 text-yellow-700 border-yellow-200";
      default:
        return "bg-gray-50 text-gray-500 border-gray-200";
    }
  };

  const getRunStatusColor = (status: TestRunStatus) => {
    switch (status) {
      case TestRunStatus.COMPLETED:
        return "bg-green-100 text-green-700";
      case TestRunStatus.IN_PROGRESS:
        return "bg-blue-100 text-blue-700";
      case TestRunStatus.CANCELLED:
        return "bg-gray-100 text-gray-700";
      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  const selectedProject = projects.find((p) => p.id === selectedProjectId);
  const selectedMilestone = milestones.find((m) => m.id === runForm.milestone_id);

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Play className="h-6 w-6 text-primary" />
            Test Runs
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Execute tests and track results
          </p>
        </div>
        {selectedProject && (
          <Button onClick={() => setCreatingRun(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Test Run
          </Button>
        )}
      </div>

      {/* Project Selector */}
      <Card className="p-4">
        <Label htmlFor="project-select">Select Project</Label>
        <select
          id="project-select"
          value={selectedProjectId || ""}
          onChange={(e) => selectTestRun(null)}
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel - Test Runs List */}
        <div className="lg:col-span-1 space-y-4">
          <Card className="p-4">
            <h2 className="font-semibold text-sm mb-3">Test Runs</h2>
            {!selectedProject ? (
              <p className="text-xs text-gray-500 text-center py-4">
                Select a project to view test runs
              </p>
            ) : testRuns.length === 0 ? (
              <div className="text-center py-8">
                <Play className="h-8 w-8 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-500">No test runs yet</p>
                <Button variant="outline" size="sm" className="mt-3" onClick={() => setCreatingRun(true)}>
                  Create First Run
                </Button>
              </div>
            ) : (
              <div className="space-y-2">
                {testRuns.map((run) => (
                  <div
                    key={run.id}
                    className={`relative group text-left p-3 rounded-lg text-sm transition-colors ${
                      selectedTestRunId === run.id
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-gray-100 border border-gray-200"
                    }`}
                  >
                    <button
                      onClick={() => selectTestRun(run.id)}
                      className="w-full"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium truncate">{run.name}</span>
                        <Badge
                          variant="outline"
                          className={selectedTestRunId === run.id ? "bg-white text-primary" : getRunStatusColor(run.status)}
                        >
                          {run.status.replace("_", " ")}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 text-xs opacity-80">
                        <span>{run.progress.total} tests</span>
                        <span>•</span>
                        <span>{run.progress.pass_rate}% pass rate</span>
                      </div>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteRunWithId(run.id);
                      }}
                      className={`absolute bottom-2 right-2 p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity ${
                        selectedTestRunId === run.id
                          ? "hover:bg-white/20 text-white"
                          : "hover:bg-red-100 text-red-600"
                      }`}
                      title="Delete test run"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Right Panel - Test Run Details / Execution */}
        <div className="lg:col-span-2">
          {!selectedTestRunId ? (
            <Card className="p-12 text-center">
              <ListTodo className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-700 mb-2">
                No Test Run Selected
              </h3>
              <p className="text-sm text-gray-500">
                Select a test run from the left to view details and execute tests.
              </p>
            </Card>
          ) : !selectedTestRun ? (
            <Card className="p-12 text-center">
              <div className="animate-pulse text-gray-400">Loading...</div>
            </Card>
          ) : (
            <>
              {/* Test Run Header */}
              <Card className="p-4 mb-4">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h2 className="text-xl font-semibold">{selectedTestRun.name}</h2>
                    <p className="text-sm text-gray-500 mt-1">
                      {selectedTestRun.description || "No description"}
                    </p>
                  </div>
                  <Badge className={getRunStatusColor(selectedTestRun.status)}>
                    {selectedTestRun.status.replace("_", " ")}
                  </Badge>
                </div>

                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="flex justify-between text-xs text-gray-600 mb-1">
                    <span>Progress</span>
                    <span>{selectedTestRun.progress.passed + selectedTestRun.progress.failed + selectedTestRun.progress.blocked} / {selectedTestRun.progress.total} executed</span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-500 transition-all"
                      style={{
                        width: `${(selectedTestRun.progress.passed / selectedTestRun.progress.total) * 100}%`,
                      }}
                    />
                  </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-5 gap-2">
                  <div className="text-center p-2 bg-green-50 rounded">
                    <div className="text-lg font-semibold text-green-700">{selectedTestRun.progress.passed}</div>
                    <div className="text-xs text-green-600">Passed</div>
                  </div>
                  <div className="text-center p-2 bg-red-50 rounded">
                    <div className="text-lg font-semibold text-red-700">{selectedTestRun.progress.failed}</div>
                    <div className="text-xs text-red-600">Failed</div>
                  </div>
                  <div className="text-center p-2 bg-orange-50 rounded">
                    <div className="text-lg font-semibold text-orange-700">{selectedTestRun.progress.blocked}</div>
                    <div className="text-xs text-orange-600">Blocked</div>
                  </div>
                  <div className="text-center p-2 bg-gray-50 rounded">
                    <div className="text-lg font-semibold text-gray-700">{selectedTestRun.progress.skipped}</div>
                    <div className="text-xs text-gray-600">Skipped</div>
                  </div>
                  <div className="text-center p-2 bg-gray-50 rounded">
                    <div className="text-lg font-semibold text-gray-700">{selectedTestRun.progress.pending}</div>
                    <div className="text-xs text-gray-600">Pending</div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 mt-4">
                  {selectedTestRun.status === TestRunStatus.PLANNED && (
                    <>
                      <Button size="sm" onClick={handleStartRun}>
                        <Play className="h-4 w-4 mr-2" />
                        Start Run
                      </Button>
                      <Button size="sm" variant="outline" onClick={handleCancelRun}>
                        <Ban className="h-4 w-4 mr-2" />
                        Cancel
                      </Button>
                    </>
                  )}
                  {selectedTestRun.status === TestRunStatus.IN_PROGRESS && (
                    <>
                      <Button size="sm" onClick={handleCompleteRun}>
                        <CheckCircle2 className="h-4 w-4 mr-2" />
                        Complete Run
                      </Button>
                      <Button size="sm" variant="outline" onClick={handleCancelRun}>
                        <Ban className="h-4 w-4 mr-2" />
                        Cancel
                      </Button>
                    </>
                  )}
                  {selectedTestRun.status === TestRunStatus.CANCELLED && (
                    <Button size="sm" variant="destructive" onClick={handleDeleteRun}>
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete Run
                    </Button>
                  )}
                  {selectedTestRun.status === TestRunStatus.COMPLETED && (
                    <Button size="sm" variant="outline" onClick={handleDeleteRun}>
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete Run
                    </Button>
                  )}
                </div>
              </Card>

              {/* Quick Actions Bar */}
              <Card className="p-3 mb-4">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm text-gray-600">Bulk actions:</span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const pendingIds = selectedTestRun.test_results.filter((r) => r.status === TestResultStatus.PENDING).map((r) => r.id);
                      handleQuickStatusUpdate(pendingIds, TestResultStatus.PASSED);
                    }}
                  >
                    All Passed
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const pendingIds = selectedTestRun.test_results.filter((r) => r.status === TestResultStatus.PENDING).map((r) => r.id);
                      handleQuickStatusUpdate(pendingIds, TestResultStatus.FAILED);
                    }}
                  >
                    All Failed
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const pendingIds = selectedTestRun.test_results.filter((r) => r.status === TestResultStatus.PENDING).map((r) => r.id);
                      handleQuickStatusUpdate(pendingIds, TestResultStatus.SKIPPED);
                    }}
                  >
                    All Skipped
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const failedIds = selectedTestRun.test_results.filter((r) => r.status === TestResultStatus.FAILED).map((r) => r.id);
                      handleQuickStatusUpdate(failedIds, TestResultStatus.RETEST);
                    }}
                  >
                    Retest Failed
                  </Button>
                </div>
              </Card>

              {/* Test Results List */}
              <div className="space-y-2">
                {selectedTestRun.test_results.map((result) => (
                  <Card
                    key={result.id}
                    className={`p-4 transition-colors ${
                      editingResultId === result.id ? "ring-2 ring-primary" : ""
                    }`}
                  >
                    {editingResultId === result.id ? (
                      // Edit Mode
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{result.test_case?.title}</span>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setEditingResultId(null);
                              setResultForm({ status: TestResultStatus.PENDING, comments: "", actual_result: "" });
                            }}
                          >
                            Cancel
                          </Button>
                        </div>
                        <div>
                          <Label>Status</Label>
                          <select
                            value={resultForm.status}
                            onChange={(e) => setResultForm({ ...resultForm, status: e.target.value as TestResultStatus })}
                            className="w-full px-3 py-2 border rounded-md text-sm"
                          >
                            <option value={TestResultStatus.PENDING}>Pending</option>
                            <option value={TestResultStatus.PASSED}>Passed</option>
                            <option value={TestResultStatus.FAILED}>Failed</option>
                            <option value={TestResultStatus.BLOCKED}>Blocked</option>
                            <option value={TestResultStatus.SKIPPED}>Skipped</option>
                          </select>
                        </div>
                        <div>
                          <Label>Actual Result</Label>
                          <Textarea
                            value={resultForm.actual_result}
                            onChange={(e) => setResultForm({ ...resultForm, actual_result: e.target.value })}
                            placeholder="Describe what actually happened..."
                            rows={2}
                          />
                        </div>
                        <div>
                          <Label>Comments</Label>
                          <Textarea
                            value={resultForm.comments}
                            onChange={(e) => setResultForm({ ...resultForm, comments: e.target.value })}
                            placeholder="Add any notes..."
                            rows={2}
                          />
                        </div>
                        {/* Evidence Upload */}
                        <div>
                          <Label>Evidence (Images/Videos)</Label>
                          <div className="space-y-2">
                            <input
                              ref={fileInputRef}
                              type="file"
                              accept="image/*,video/*"
                              onChange={handleFileSelect}
                              className="hidden"
                            />
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={() => fileInputRef.current?.click()}
                              disabled={uploadingEvidence}
                            >
                              <Upload className="h-4 w-4 mr-2" />
                              {uploadingEvidence ? "Uploading..." : "Upload Evidence"}
                            </Button>
                            <p className="text-xs text-gray-500">Supported: Images (JPG, PNG, GIF, WEBP), Videos (MP4, WEBM, MOV). Max 20MB</p>
                            {/* Display existing evidence for this result */}
                            {result.evidence && result.evidence.length > 0 && (
                              <div className="flex flex-wrap gap-2 mt-2">
                                {result.evidence.map((evidence) => (
                                  <div key={evidence.id} className="relative group">
                                    {evidence.type === "image" ? (
                                      <a
                                        href={getEvidenceUrl(evidence.id, token)}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="block"
                                      >
                                        <img
                                          src={getEvidenceUrl(evidence.id, token)}
                                          alt={evidence.filename}
                                          className="h-16 w-16 object-cover rounded border border-gray-200"
                                        />
                                      </a>
                                    ) : (
                                      <a
                                        href={getEvidenceUrl(evidence.id, token)}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="block relative"
                                      >
                                        <div className="h-16 w-16 bg-gray-100 rounded border border-gray-200 flex items-center justify-center">
                                          <Video className="h-6 w-6 text-gray-400" />
                                        </div>
                                      </a>
                                    )}
                                    <Button
                                      type="button"
                                      variant="destructive"
                                      size="icon"
                                      className="absolute -top-2 -right-2 h-5 w-5 opacity-0 group-hover:opacity-100 transition-opacity"
                                      onClick={() => handleDeleteEvidence(result.id, evidence.id)}
                                    >
                                      <X className="h-3 w-3" />
                                    </Button>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                        <Button onClick={() => handleUpdateResult(result.id, resultForm)}>
                          Save Result
                        </Button>
                      </div>
                    ) : (
                      // View Mode
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3 flex-1">
                          <button
                            onClick={() => {
                              setResultForm({
                                status: result.status,
                                comments: result.comments || "",
                                actual_result: result.actual_result || "",
                              });
                              setEditingResultId(result.id);
                            }}
                            className="mt-1"
                          >
                            {getStatusIcon(result.status)}
                          </button>
                          <div className="flex-1">
                            <h4 className="font-medium">{result.test_case?.title}</h4>
                            {result.comments && (
                              <p className="text-sm text-gray-600 mt-1">{result.comments}</p>
                            )}
                            {result.actual_result && (
                              <p className="text-sm text-gray-500 mt-1 italic">{result.actual_result}</p>
                            )}
                            {/* Evidence thumbnails */}
                            {result.evidence && result.evidence.length > 0 && (
                              <div className="flex flex-wrap gap-2 mt-2">
                                {result.evidence.map((evidence) => (
                                  <a
                                    key={evidence.id}
                                    href={getEvidenceUrl(evidence.id, token)}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-block"
                                    title={`${evidence.filename} (${formatFileSize(evidence.size_bytes)})`}
                                  >
                                    {evidence.type === "image" ? (
                                      <img
                                        src={getEvidenceUrl(evidence.id, token)}
                                        alt={evidence.filename}
                                        className="h-12 w-12 object-cover rounded border border-gray-200 hover:border-primary transition-colors"
                                      />
                                    ) : (
                                      <div className="h-12 w-12 bg-gray-100 rounded border border-gray-200 flex items-center justify-center hover:border-primary transition-colors">
                                        <Video className="h-5 w-5 text-gray-400" />
                                      </div>
                                    )}
                                  </a>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className={getStatusColor(result.status)}>
                            {result.status}
                          </Badge>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => {
                              setResultForm({
                                status: result.status,
                                comments: result.comments || "",
                                actual_result: result.actual_result || "",
                              });
                              setEditingResultId(result.id);
                            }}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    )}
                  </Card>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Create Test Run Dialog */}
      <Dialog open={isCreatingRun} onOpenChange={setCreatingRun}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Test Run</DialogTitle>
            <DialogDescription>
              Create a new test run for "{selectedProject?.name}"
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="run-name">Run Name *</Label>
              <Input
                id="run-name"
                value={runForm.name}
                onChange={(e) => setRunForm({ ...runForm, name: e.target.value })}
                placeholder="e.g., Sprint 15 Regression, QA Build 123"
              />
            </div>
            <div>
              <Label htmlFor="run-description">Description</Label>
              <Textarea
                id="run-description"
                value={runForm.description}
                onChange={(e) => setRunForm({ ...runForm, description: e.target.value })}
                placeholder="What is being tested..."
                rows={2}
              />
            </div>
            <div>
              <Label htmlFor="run-milestone">Milestone (optional)</Label>
              <select
                id="run-milestone"
                value={runForm.milestone_id || ""}
                onChange={(e) => setRunForm({ ...runForm, milestone_id: e.target.value ? parseInt(e.target.value) : undefined })}
                className="w-full px-3 py-2 border rounded-md text-sm bg-white"
              >
                <option value="">No milestone</option>
                {milestones.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </select>
              <Button
                variant="link"
                size="sm"
                className="text-xs p-0 mt-1"
                onClick={() => {
                  // For now, just show a toast
                  toast.info("Create milestones from the project settings");
                }}
              >
                + Create new milestone
              </Button>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreatingRun(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateRun} disabled={!runForm.name}>
              Create Run
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
