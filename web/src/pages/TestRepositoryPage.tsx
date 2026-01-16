// src/pages/TestRepositoryPage.tsx
// Test Management / Repository Page - Similar to TestRail

import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router";
import { useAuthStore } from "@/store/auth.store";
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
  FolderOpen,
  FileText,
  Plus,
  Search,
  ChevronRight,
  MoreVertical,
  Edit,
  Trash2,
  Save,
  Folder,
  FolderPlus,
  Download,
  Upload,
  RefreshCw,
  History,
  RotateCcw,
  Eye,
} from "lucide-react";
import type {
  TestCaseType,
  Priority,
  AutomationStatus,
  RepositoryTestCase,
  TestCaseVersion,
} from "@/api/testRepository";
import { toast } from "sonner";
import { TestCaseTypeLabel, PriorityLabel, PriorityColor, AutomationStatusLabel } from "@/lib/testRepositoryUtils";

export default function TestRepositoryPage() {
  const token = useAuthStore((state) => state.token);
  const navigate = useNavigate();
  const location = useLocation();
  const {
    // State
    projects,
    selectedProjectId,
    suites,
    selectedSuiteId,
    testCases,
    testCasesTotal,
    testCasesLoading,
    testCasesFilter,
    isCreatingProject,
    isCreatingSuite,
    isCreatingTestCase,
    isEditingTestCase,
    isEditingSuite,
    editingSuiteId,
    selectedTestCaseId,

    // Actions
    fetchProjects,
    createProject,
    selectProject,
    fetchSuites,
    createSuite,
    updateSuite,
    deleteSuite,
    selectSuite,
    setEditingSuite,
    fetchTestCases,
    createTestCase,
    updateTestCase,
    deleteTestCase,
    setTestCasesFilter,
    setCreatingProject,
    setCreatingSuite,
    setCreatingTestCase,
    setEditingTestCase,
    selectTestCase,
  } = useTestRepository();

  // Local form states
  const [projectForm, setProjectForm] = useState({ name: "", description: "" });
  const [suiteForm, setSuiteForm] = useState({ name: "", description: "" });
  const [testCaseForm, setTestCaseForm] = useState({
    title: "",
    description: "",
    tc_type: "functional" as TestCaseType,
    priority: "medium" as Priority,
    automation_status: "manual" as AutomationStatus,
    estimated_minutes: "",
    preconditions: [] as string[],
    steps: [] as Array<{ step: number; action: string; expected: string }>,
    expected_result: "",
    tags: [] as string[],
  });
  const [searchQuery, setSearchQuery] = useState("");
  const [showVersionsDialog, setShowVersionsDialog] = useState(false);
  const [versions, setVersions] = useState<TestCaseVersion[]>([]);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [changeSummary, setChangeSummary] = useState("");

  // Load projects on mount
  useEffect(() => {
    if (token) {
      fetchProjects(token);
    }
  }, [token, fetchProjects]);

  // Load suites when project selected
  useEffect(() => {
    if (selectedProjectId && token) {
      fetchSuites(selectedProjectId, token);
    }
  }, [selectedProjectId, token, fetchSuites]);

  // Load test cases when filter changes
  useEffect(() => {
    if (token && (selectedSuiteId || selectedProjectId)) {
      fetchTestCases(token);
    }
  }, [testCasesFilter, token, selectedSuiteId, selectedProjectId, fetchTestCases]);

  // Handle navigation state (from history page or orchestrator)
  useEffect(() => {
    const state = location.state as { projectId?: number; suiteId?: number } | null;
    if (state?.projectId && projects.length > 0) {
      selectProject(state.projectId);
      if (state.suiteId) {
        // Small delay to ensure suites are loaded
        setTimeout(() => selectSuite(state.suiteId), 100);
      }
    }
  }, [location.state, projects, selectProject, selectSuite]);

  // Handlers
  const handleCreateProject = async () => {
    if (!token) return;
    await createProject(projectForm, token);
    setProjectForm({ name: "", description: "" });
    setCreatingProject(false);
  };

  const handleCreateSuite = async () => {
    if (!token || !selectedProjectId) return;
    try {
      await createSuite({ ...suiteForm, project_id: selectedProjectId }, token);
      setSuiteForm({ name: "", description: "" });
      setCreatingSuite(false);
      toast.success("Suite created successfully");
    } catch (error: any) {
      toast.error(error.message || "Failed to create suite");
    }
  };

  const handleEditSuite = async () => {
    if (!token || !editingSuiteId) return;
    try {
      await updateSuite(editingSuiteId, suiteForm, token);
      setSuiteForm({ name: "", description: "" });
      setEditingSuite(false);
      toast.success("Suite updated successfully");
    } catch (error: any) {
      toast.error(error.message || "Failed to update suite");
    }
  };

  const handleDeleteSuite = async (suiteId: number) => {
    if (!token) return;
    if (confirm("Are you sure you want to delete this suite? All test cases in this suite will also be deleted.")) {
      try {
        await deleteSuite(suiteId, token);
        if (selectedSuiteId === suiteId) {
          selectSuite(null);
        }
      } catch (error: any) {
        toast.error(error.message || "Failed to delete suite");
      }
    }
  };

  const handleEditSuiteClick = (suite: { id: number; name: string; description?: string }) => {
    setSuiteForm({ name: suite.name, description: suite.description || "" });
    setEditingSuite(true, suite.id);
  };

  const handleRegenerateTestCase = (testCase: RepositoryTestCase) => {
    // Navigate to orchestrator with test case data for regeneration
    navigate("/orchestrator", {
      state: {
        regenerateTestCase: {
          id: testCase.id,
          title: testCase.title,
          description: testCase.description,
          tc_type: testCase.tc_type,
          priority: testCase.priority,
          preconditions: testCase.preconditions,
          steps: testCase.steps,
          expected_result: testCase.expected_result,
          suite_id: testCase.suite_id,
        }
      }
    });
  };

  const handleCreateTestCase = async () => {
    if (!token || !selectedSuiteId) return;
    await createTestCase(
      {
        ...testCaseForm,
        estimated_minutes: testCaseForm.estimated_minutes
          ? parseInt(testCaseForm.estimated_minutes)
          : undefined,
      },
      token
    );
    setTestCaseForm({
      title: "",
      description: "",
      tc_type: "functional",
      priority: "medium",
      automation_status: "manual",
      estimated_minutes: "",
      preconditions: [],
      steps: [],
      expected_result: "",
      tags: [],
    });
    setCreatingTestCase(false);
  };

  const handleAddStep = () => {
    const stepNumber = testCaseForm.steps.length + 1;
    setTestCaseForm({
      ...testCaseForm,
      steps: [
        ...testCaseForm.steps,
        { step: stepNumber, action: "", expected: "" },
      ],
    });
  };

  const handleUpdateStep = (
    index: number,
    field: "action" | "expected",
    value: string
  ) => {
    const newSteps = [...testCaseForm.steps];
    newSteps[index][field] = value;
    setTestCaseForm({ ...testCaseForm, steps: newSteps });
  };

  const handleRemoveStep = (index: number) => {
    const newSteps = testCaseForm.steps.filter((_, i) => i !== index);
    // Renumber steps
    const renumbered = newSteps.map((s, i) => ({ ...s, step: i + 1 }));
    setTestCaseForm({ ...testCaseForm, steps: renumbered });
  };

  // Version control handlers
  const handleViewVersions = async (testCaseId: number) => {
    if (!token) return;
    setVersionsLoading(true);
    setShowVersionsDialog(true);
    try {
      const { getTestCaseVersions } = await import("@/api/testRepository");
      const data = await getTestCaseVersions(testCaseId, token);
      setVersions(data.versions);
    } catch (error: any) {
      toast.error(error.message || "Failed to load version history");
    } finally {
      setVersionsLoading(false);
    }
  };

  const handleRestoreVersion = async (testCaseId: number, versionId: number) => {
    if (!token) return;
    if (!confirm("Are you sure you want to restore this version? The current version will be saved as a new version.")) {
      return;
    }
    try {
      const { restoreTestCaseVersion } = await import("@/api/testRepository");
      await restoreTestCaseVersion(testCaseId, versionId, changeSummary, token);
      toast.success("Version restored successfully");
      setShowVersionsDialog(false);
      // Refresh test cases
      fetchTestCases(token);
    } catch (error: any) {
      toast.error(error.message || "Failed to restore version");
    }
  };

  const handleSearch = (value: string) => {
    setSearchQuery(value);
    setTestCasesFilter({ search: value || undefined });
  };

  const selectedProject = projects.find((p) => p.id === selectedProjectId);
  const selectedSuite = suites.find((s) => s.id === selectedSuiteId);
  const selectedTestCase = testCases.find((tc) => tc.id === selectedTestCaseId);

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <FolderOpen className="h-6 w-6 text-primary" />
            Test Repository
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage your test cases in an organized repository
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Upload className="h-4 w-4 mr-2" />
            Import
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Panel - Projects & Suites */}
        <div className="lg:col-span-1 space-y-4">
          {/* Projects */}
          <Card className="p-4">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold text-sm">Projects</h2>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={() => setCreatingProject(true)}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>

            <div className="space-y-1">
              {projects.length === 0 ? (
                <p className="text-xs text-gray-500 text-center py-4">
                  No projects yet
                </p>
              ) : (
                projects.map((project) => (
                  <button
                    key={project.id}
                    onClick={() => selectProject(project.id)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm flex items-center justify-between transition-colors ${
                      selectedProjectId === project.id
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-gray-100"
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <Folder
                        className={`h-4 w-4 flex-shrink-0 ${
                          selectedProjectId === project.id
                            ? "text-primary-foreground"
                            : "text-gray-400"
                        }`}
                      />
                      <span className="truncate">{project.name}</span>
                    </div>
                    <Badge
                      variant={
                        selectedProjectId === project.id ? "secondary" : "outline"
                      }
                      className="text-xs"
                    >
                      {project.case_count}
                    </Badge>
                  </button>
                ))
              )}
            </div>
          </Card>

          {/* Suites */}
          {selectedProject && (
            <Card className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-semibold text-sm">Suites</h2>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => setCreatingSuite(true)}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>

              <div className="space-y-1">
                {suites.length === 0 ? (
                  <p className="text-xs text-gray-500 text-center py-4">
                    No suites yet
                  </p>
                ) : (
                  suites.map((suite) => (
                    <div
                      key={suite.id}
                      className={`group flex items-center justify-between px-2 py-1 rounded-lg text-sm transition-colors ${
                        selectedSuiteId === suite.id
                          ? "bg-primary text-primary-foreground"
                          : "hover:bg-gray-100"
                      }`}
                    >
                      <button
                        onClick={() => selectSuite(suite.id)}
                        className="flex-1 text-left flex items-center gap-2 truncate"
                      >
                        <FolderOpen
                          className={`h-4 w-4 flex-shrink-0 ${
                            selectedSuiteId === suite.id
                              ? "text-primary-foreground"
                              : "text-gray-400"
                          }`}
                        />
                        <span className="truncate">{suite.name}</span>
                      </button>
                      <div className="flex items-center gap-1">
                        <Badge
                          variant={
                            selectedSuiteId === suite.id ? "secondary" : "outline"
                          }
                          className="text-xs"
                        >
                          {suite.case_count}
                        </Badge>
                        <Button
                          variant="ghost"
                          size="icon"
                          className={`h-6 w-6 ${
                            selectedSuiteId === suite.id
                              ? "hover:bg-primary-foreground/20 text-primary-foreground"
                              : "hover:bg-gray-200"
                          }`}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEditSuiteClick(suite);
                          }}
                        >
                          <Edit className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className={`h-6 w-6 text-destructive ${
                            selectedSuiteId === suite.id
                              ? "hover:bg-primary-foreground/20 text-primary-foreground"
                              : "hover:bg-red-100"
                          }`}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteSuite(suite.id);
                          }}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>
          )}
        </div>

        {/* Right Panel - Test Cases */}
        <div className="lg:col-span-3">
          {!selectedProject ? (
            <Card className="p-12 text-center">
              <Folder className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-700 mb-2">
                No Project Selected
              </h3>
              <p className="text-sm text-gray-500">
                Select a project from the left or create a new one to get started.
              </p>
            </Card>
          ) : !selectedSuite ? (
            <Card className="p-12 text-center">
              <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-700 mb-2">
                No Suite Selected
              </h3>
              <p className="text-sm text-gray-500">
                Select a suite from the left or create a new one to view test cases.
              </p>
            </Card>
          ) : (
            <>
              {/* Suite Header */}
              <Card className="p-4 mb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FolderOpen className="h-5 w-5 text-primary" />
                    <div>
                      <h2 className="font-semibold">{selectedSuite?.name}</h2>
                      <p className="text-xs text-gray-500">
                        {testCasesTotal} test case{testCasesTotal !== 1 ? "s" : ""}
                      </p>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => setCreatingTestCase(true)}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    New Test Case
                  </Button>
                </div>
              </Card>

              {/* Search & Filters */}
              <Card className="p-4 mb-4">
                <div className="flex items-center gap-4">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      placeholder="Search test cases..."
                      value={searchQuery}
                      onChange={(e) => handleSearch(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                  <select
                    className="px-3 py-2 border rounded-md text-sm bg-white"
                    value={testCasesFilter.tc_type || "all"}
                    onChange={(e) =>
                      setTestCasesFilter({
                        tc_type:
                          e.target.value === "all"
                            ? undefined
                            : (e.target.value as TestCaseType),
                      })
                    }
                  >
                    <option value="all">All Types</option>
                    <option value="functional">Functional</option>
                    <option value="negative">Negative</option>
                    <option value="boundary">Boundary</option>
                    <option value="ui">UI</option>
                    <option value="api">API</option>
                  </select>
                  <select
                    className="px-3 py-2 border rounded-md text-sm bg-white"
                    value={testCasesFilter.priority || "all"}
                    onChange={(e) =>
                      setTestCasesFilter({
                        priority:
                          e.target.value === "all"
                            ? undefined
                            : (e.target.value as Priority),
                      })
                    }
                  >
                    <option value="all">All Priorities</option>
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
              </Card>

              {/* Test Cases List */}
              {testCasesLoading ? (
                <Card className="p-8 text-center">
                  <div className="animate-pulse text-gray-400">Loading...</div>
                </Card>
              ) : testCases.length === 0 ? (
                <Card className="p-12 text-center">
                  <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-700 mb-2">
                    No Test Cases
                  </h3>
                  <p className="text-sm text-gray-500 mb-4">
                    Create your first test case or import from Orchestrator.
                  </p>
                  <Button size="sm" onClick={() => setCreatingTestCase(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Create Test Case
                  </Button>
                </Card>
              ) : (
                <div className="space-y-2">
                  {testCases.map((testCase) => (
                    <Card
                      key={testCase.id}
                      className={`p-4 cursor-pointer transition-colors ${
                        selectedTestCaseId === testCase.id
                          ? "border-primary ring-1 ring-primary"
                          : "hover:bg-gray-50"
                      }`}
                      onClick={() => selectTestCase(testCase.id)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3 flex-1 min-w-0">
                          <div className="flex flex-col items-center gap-1">
                            <Badge
                              variant="outline"
                              className={PriorityColor(testCase.priority)}
                            >
                              {PriorityLabel(testCase.priority)}
                            </Badge>
                            <Badge variant="secondary" className="text-xs">
                              {TestCaseTypeLabel(testCase.tc_type)}
                            </Badge>
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <h4 className="font-medium truncate">
                                {testCase.external_id && (
                                  <span className="text-gray-500 mr-2">
                                    {testCase.external_id}:
                                  </span>
                                )}
                                {testCase.title}
                              </h4>
                              {testCase.is_draft && (
                                <Badge variant="outline" className="text-xs">
                                  Draft
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-gray-500 truncate mt-1">
                              {testCase.description || "No description"}
                            </p>
                            <div className="flex items-center gap-2 mt-2">
                              <Badge
                                variant="outline"
                                className="text-xs bg-white"
                              >
                                {testCase.step_count} steps
                              </Badge>
                              {testCase.estimated_minutes && (
                                <Badge
                                  variant="outline"
                                  className="text-xs bg-white"
                                >
                                  {testCase.estimated_minutes}m
                                </Badge>
                              )}
                              {testCase.tags && testCase.tags.length > 0 && (
                                <div className="flex gap-1">
                                  {testCase.tags.slice(0, 2).map((tag) => (
                                    <Badge
                                      key={tag}
                                      variant="outline"
                                      className="text-xs bg-gray-100"
                                    >
                                      {tag}
                                    </Badge>
                                  ))}
                                  {testCase.tags.length > 2 && (
                                    <Badge
                                      variant="outline"
                                      className="text-xs bg-gray-100"
                                    >
                                      +{testCase.tags.length - 2}
                                    </Badge>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          <Badge
                            variant="outline"
                            className="text-xs"
                            style={{
                              backgroundColor:
                                testCase.automation_status === "automated"
                                  ? "#dcfce7"
                                  : undefined,
                            }}
                          >
                            {AutomationStatusLabel(testCase.automation_status)}
                          </Badge>
                          <Badge
                            variant="secondary"
                            className="text-xs font-mono"
                            title="Version number"
                          >
                            v{testCase.version || 1}
                          </Badge>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            title="View version history"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleViewVersions(testCase.id);
                            }}
                          >
                            <History className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            title="Re-generate with AI"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRegenerateTestCase(testCase);
                            }}
                          >
                            <RefreshCw className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={(e) => {
                              e.stopPropagation();
                              // Handle edit
                            }}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive"
                            onClick={(e) => {
                              e.stopPropagation();
                              if (confirm("Delete this test case?")) {
                                deleteTestCase(testCase.id, token!);
                              }
                            }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Create Project Dialog */}
      <Dialog open={isCreatingProject} onOpenChange={setCreatingProject}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Project</DialogTitle>
            <DialogDescription>
              Create a new project to organize your test suites and test cases.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="project-name">Project Name *</Label>
              <Input
                id="project-name"
                value={projectForm.name}
                onChange={(e) =>
                  setProjectForm({ ...projectForm, name: e.target.value })
                }
                placeholder="e.g., E-Commerce, Mobile App"
              />
            </div>
            <div>
              <Label htmlFor="project-description">Description</Label>
              <Textarea
                id="project-description"
                value={projectForm.description}
                onChange={(e) =>
                  setProjectForm({ ...projectForm, description: e.target.value })
                }
                placeholder="Brief description of the project..."
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreatingProject(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateProject} disabled={!projectForm.name}>
              Create Project
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create/Edit Suite Dialog */}
      <Dialog open={isCreatingSuite || isEditingSuite} onOpenChange={(open) => {
        if (!open) {
          setCreatingSuite(false);
          setEditingSuite(false);
        }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{isEditingSuite ? "Edit Suite" : "Create New Suite"}</DialogTitle>
            <DialogDescription>
              {isEditingSuite
                ? `Edit suite "${suites.find(s => s.id === editingSuiteId)?.name}"`
                : `Create a new test suite within "${selectedProject?.name}"`
              }
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="suite-name">Suite Name *</Label>
              <Input
                id="suite-name"
                value={suiteForm.name}
                onChange={(e) =>
                  setSuiteForm({ ...suiteForm, name: e.target.value })
                }
                placeholder="e.g., Checkout Flow, User Authentication"
              />
            </div>
            <div>
              <Label htmlFor="suite-description">Description</Label>
              <Textarea
                id="suite-description"
                value={suiteForm.description}
                onChange={(e) =>
                  setSuiteForm({ ...suiteForm, description: e.target.value })
                }
                placeholder="Brief description of the test suite..."
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setCreatingSuite(false);
              setEditingSuite(false);
            }}>
              Cancel
            </Button>
            <Button
              onClick={isEditingSuite ? handleEditSuite : handleCreateSuite}
              disabled={!suiteForm.name}
            >
              {isEditingSuite ? "Save Changes" : "Create Suite"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Test Case Dialog */}
      <Dialog
        open={isCreatingTestCase}
        onOpenChange={setCreatingTestCase}
      >
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create New Test Case</DialogTitle>
            <DialogDescription>
              Create a new test case in "{selectedSuite?.name}"
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {/* Title */}
            <div>
              <Label htmlFor="tc-title">Title *</Label>
              <Input
                id="tc-title"
                value={testCaseForm.title}
                onChange={(e) =>
                  setTestCaseForm({ ...testCaseForm, title: e.target.value })
                }
                placeholder="e.g., User can complete checkout with valid payment"
              />
            </div>

            {/* Description */}
            <div>
              <Label htmlFor="tc-description">Description</Label>
              <Textarea
                id="tc-description"
                value={testCaseForm.description}
                onChange={(e) =>
                  setTestCaseForm({ ...testCaseForm, description: e.target.value })
                }
                placeholder="Detailed description of what is being tested..."
                rows={2}
              />
            </div>

            {/* Type, Priority, Automation Status */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="tc-type">Type</Label>
                <select
                  id="tc-type"
                  value={testCaseForm.tc_type}
                  onChange={(e) =>
                    setTestCaseForm({
                      ...testCaseForm,
                      tc_type: e.target.value as TestCaseType,
                    })
                  }
                  className="w-full px-3 py-2 border rounded-md text-sm"
                >
                  <option value="functional">Functional</option>
                  <option value="negative">Negative</option>
                  <option value="boundary">Boundary</option>
                  <option value="ui">UI</option>
                  <option value="api">API</option>
                  <option value="integration">Integration</option>
                  <option value="performance">Performance</option>
                  <option value="security">Security</option>
                </select>
              </div>
              <div>
                <Label htmlFor="tc-priority">Priority</Label>
                <select
                  id="tc-priority"
                  value={testCaseForm.priority}
                  onChange={(e) =>
                    setTestCaseForm({
                      ...testCaseForm,
                      priority: e.target.value as Priority,
                    })
                  }
                  className="w-full px-3 py-2 border rounded-md text-sm"
                >
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
              <div>
                <Label htmlFor="tc-automation">Automation</Label>
                <select
                  id="tc-automation"
                  value={testCaseForm.automation_status}
                  onChange={(e) =>
                    setTestCaseForm({
                      ...testCaseForm,
                      automation_status: e.target.value as AutomationStatus,
                    })
                  }
                  className="w-full px-3 py-2 border rounded-md text-sm"
                >
                  <option value="manual">Manual</option>
                  <option value="automated">Automated</option>
                  <option value="to_be_automated">To Be Automated</option>
                  <option value="none">None</option>
                </select>
              </div>
            </div>

            {/* Estimated Time */}
            <div>
              <Label htmlFor="tc-time">Estimated Time (minutes)</Label>
              <Input
                id="tc-time"
                type="number"
                value={testCaseForm.estimated_minutes}
                onChange={(e) =>
                  setTestCaseForm({
                    ...testCaseForm,
                    estimated_minutes: e.target.value,
                  })
                }
                placeholder="e.g., 10"
              />
            </div>

            {/* Preconditions */}
            <div>
              <Label htmlFor="tc-preconditions">Preconditions (one per line)</Label>
              <Textarea
                id="tc-preconditions"
                value={testCaseForm.preconditions.join("\n")}
                onChange={(e) =>
                  setTestCaseForm({
                    ...testCaseForm,
                    preconditions: e.target.value
                      .split("\n")
                      .filter((line) => line.trim()),
                  })
                }
                placeholder="User is logged in&#10;Cart has items&#10;Payment gateway is available"
                rows={3}
              />
            </div>

            {/* Steps */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label>Test Steps</Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleAddStep}
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add Step
                </Button>
              </div>
              {testCaseForm.steps.length === 0 ? (
                <div className="text-center py-4 border rounded-md border-dashed">
                  <p className="text-sm text-gray-500">No steps added yet</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {testCaseForm.steps.map((step, index) => (
                    <div key={index} className="border rounded-md p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">
                          Step {step.step}
                        </span>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 text-destructive"
                          onClick={() => handleRemoveStep(index)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                      <div className="space-y-2">
                        <Input
                          placeholder="Action..."
                          value={step.action}
                          onChange={(e) =>
                            handleUpdateStep(index, "action", e.target.value)
                          }
                        />
                        <Input
                          placeholder="Expected result..."
                          value={step.expected}
                          onChange={(e) =>
                            handleUpdateStep(index, "expected", e.target.value)
                          }
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Expected Result */}
            <div>
              <Label htmlFor="tc-expected">Expected Result (overall)</Label>
              <Textarea
                id="tc-expected"
                value={testCaseForm.expected_result}
                onChange={(e) =>
                  setTestCaseForm({
                    ...testCaseForm,
                    expected_result: e.target.value,
                  })
                }
                placeholder="Overall expected result of the test..."
                rows={2}
              />
            </div>

            {/* Tags */}
            <div>
              <Label htmlFor="tc-tags">Tags (comma-separated)</Label>
              <Input
                id="tc-tags"
                value={testCaseForm.tags.join(", ")}
                onChange={(e) =>
                  setTestCaseForm({
                    ...testCaseForm,
                    tags: e.target.value
                      .split(",")
                      .map((t) => t.trim())
                      .filter((t) => t),
                  })
                }
                placeholder="e.g., checkout, payment, critical"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreatingTestCase(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateTestCase} disabled={!testCaseForm.title}>
              Create Test Case
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Version History Dialog */}
      <Dialog open={showVersionsDialog} onOpenChange={setShowVersionsDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <History className="h-5 w-5" />
              Version History
            </DialogTitle>
            <DialogDescription>
              View and restore previous versions of this test case
            </DialogDescription>
          </DialogHeader>

          {versionsLoading ? (
            <div className="py-8 text-center text-gray-500">Loading...</div>
          ) : versions.length === 0 ? (
            <div className="py-8 text-center text-gray-500">
              No version history available
            </div>
          ) : (
            <div className="space-y-3">
              {versions.map((version) => (
                <Card key={version.id} className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="outline" className="font-mono">
                          v{version.version}
                        </Badge>
                        <span className="text-sm text-gray-500">
                          {new Date(version.created_at).toLocaleString()}
                        </span>
                        {version.change_summary && (
                          <span className="text-sm text-gray-600 italic">
                            - {version.change_summary}
                          </span>
                        )}
                      </div>
                      <h4 className="font-medium">{version.title}</h4>
                      <p className="text-sm text-gray-500 line-clamp-2 mt-1">
                        {version.description || "No description"}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant="secondary" className="text-xs">
                          {TestCaseTypeLabel(version.tc_type)}
                        </Badge>
                        <Badge
                          variant="outline"
                          className={`text-xs ${PriorityColor(version.priority)}`}
                        >
                          {PriorityLabel(version.priority)}
                        </Badge>
                        <span className="text-xs text-gray-500">
                          {version.steps?.length || 0} steps
                        </span>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleRestoreVersion(selectedTestCaseId!, version.id)}
                      className="gap-1"
                    >
                      <RotateCcw className="h-4 w-4" />
                      Restore
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          )}

          <div className="mt-4 pt-4 border-t">
            <Label htmlFor="change-summary">Change Summary (optional)</Label>
            <Input
              id="change-summary"
              placeholder="Describe why you're restoring this version..."
              value={changeSummary}
              onChange={(e) => setChangeSummary(e.target.value)}
            />
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowVersionsDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
