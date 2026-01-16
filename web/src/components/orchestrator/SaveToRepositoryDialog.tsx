// src/components/orchestrator/SaveToRepositoryDialog.tsx
// Dialog for saving Orchestrator results to Test Repository

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { FolderPlus, Check, AlertCircle, Plus } from "lucide-react";
import { useTestRepository } from "@/store/testRepository.store";
import { useAuthStore } from "@/store/auth.store";
import { orchestratorToRepositoryTestCase } from "@/lib/testRepositoryUtils";
import type { TestCaseType } from "@/api/testRepository";
import { toast } from "sonner";

interface Props {
  open: boolean;
  onClose: () => void;
  orchestratorResult: any;
}

export default function SaveToRepositoryDialog({
  open,
  onClose,
  orchestratorResult,
}: Props) {
  const token = useAuthStore((state) => state.token);
  const { projects, fetchProjects, suites, fetchSuites, saveFromOrchestrator } = useTestRepository();

  // Form state
  const [mode, setMode] = useState<"existing" | "new">("existing");
  const [projectId, setProjectId] = useState<number | null>(null);
  const [projectName, setProjectName] = useState("");
  const [suiteId, setSuiteId] = useState<number | null>(null);
  const [suiteName, setSuiteName] = useState("");
  const [suiteMode, setSuiteMode] = useState<"existing" | "new">("existing");
  const [selectedTestCases, setSelectedTestCases] = useState<Set<string>>(new Set());
  const [saving, setSaving] = useState(false);

  // Load projects when dialog opens
  useEffect(() => {
    if (open && token) {
      fetchProjects(token);
    }
  }, [open, token, fetchProjects]);

  // Load suites when project is selected
  useEffect(() => {
    if (projectId && token) {
      fetchSuites(projectId, token);
    }
  }, [projectId, token, fetchSuites]);

  // Reset form when opening with new result
  useEffect(() => {
    if (open && orchestratorResult) {
      // Reset modes
      setMode("existing");
      setSuiteMode("existing");
      setProjectId(null);
      setSuiteId(null);
      setProjectName("");
      setSuiteName("");

      // Select all test cases by default
      const allIds = new Set<string>();
      orchestratorResult.functional?.forEach((tc: any) => allIds.add(`F-${tc.tc_id}`));
      orchestratorResult.negative?.forEach((tc: any) => allIds.add(`N-${tc.tc_id}`));
      orchestratorResult.boundary?.forEach((tc: any) => allIds.add(`B-${tc.tc_id}`));
      setSelectedTestCases(allIds);
    }
  }, [open, orchestratorResult]);

  const allTestCases = [
    ...(orchestratorResult?.functional?.map((tc: any) => ({ ...tc, type: "functional" as TestCaseType })) || []),
    ...(orchestratorResult?.negative?.map((tc: any) => ({ ...tc, type: "negative" as TestCaseType })) || []),
    ...(orchestratorResult?.boundary?.map((tc: any) => ({ ...tc, type: "boundary" as TestCaseType })) || []),
  ];

  const selectedCount = selectedTestCases.size;
  const totalCount = allTestCases.length;

  const toggleTestCase = (id: string) => {
    const newSet = new Set(selectedTestCases);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    setSelectedTestCases(newSet);
  };

  const toggleAll = () => {
    if (selectedCount === totalCount) {
      setSelectedTestCases(new Set());
    } else {
      const allIds = new Set<string>();
      allTestCases.forEach((tc) => allIds.add(`${tc.type.charAt(0).toUpperCase()}-${tc.tc_id}`));
      setSelectedTestCases(allIds);
    }
  };

  const handleSave = async () => {
    if (!token) return;

    // Validation
    if (mode === "existing") {
      if (!projectId) {
        toast.error("Please select a project");
        return;
      }
      if (suiteMode === "existing" && !suiteId) {
        toast.error("Please select a suite");
        return;
      }
      if (suiteMode === "new" && !suiteName.trim()) {
        toast.error("Please enter a suite name");
        return;
      }
    } else {
      if (!projectName.trim()) {
        toast.error("Please enter a project name");
        return;
      }
      if (!suiteName.trim()) {
        toast.error("Please enter a suite name");
        return;
      }
    }

    if (selectedCount === 0) {
      toast.error("Please select at least one test case");
      return;
    }

    setSaving(true);

    try {
      // Convert selected test cases to repository format
      const testCasesToSave = allTestCases
        .filter((tc) => selectedTestCases.has(`${tc.type.charAt(0).toUpperCase()}-${tc.tc_id}`))
        .map((tc) => orchestratorToRepositoryTestCase(tc, tc.type));

      await saveFromOrchestrator(
        {
          project_id: mode === "existing" ? projectId! : undefined,
          project_name: mode === "new" ? projectName : undefined,
          suite_id: mode === "existing" && suiteMode === "existing" ? suiteId! : undefined,
          suite_name: (mode === "existing" && suiteMode === "new" && suiteName.trim()) ? suiteName : (mode === "new" ? suiteName : undefined),
          test_cases: testCasesToSave,
          source_session_id: orchestratorResult.session_id,
        },
        token
      );

      toast.success(
        `Successfully saved ${selectedCount} test case${selectedCount > 1 ? "s" : ""} to repository!`
      );
      onClose();
    } catch (error: any) {
      toast.error(error.message || "Failed to save to repository");
    } finally {
      setSaving(false);
    }
  };

  const selectedProject = projects.find((p) => p.id === projectId);

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FolderPlus className="h-5 w-5 text-primary" />
            Save to Test Repository
          </DialogTitle>
          <DialogDescription>
            Save these generated test cases to your repository for future use and reuse.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Mode Toggle */}
          <div className="flex gap-2">
            <Button
              type="button"
              variant={mode === "existing" ? "default" : "outline"}
              onClick={() => setMode("existing")}
              className="flex-1"
            >
              Use Existing Project
            </Button>
            <Button
              type="button"
              variant={mode === "new" ? "default" : "outline"}
              onClick={() => setMode("new")}
              className="flex-1"
            >
              Create New Project
            </Button>
          </div>

          {/* Existing Project/Suite Selection */}
          {mode === "existing" && (
            <>
              <div>
                <Label htmlFor="project-select">Project *</Label>
                <select
                  id="project-select"
                  value={projectId || ""}
                  onChange={(e) => {
                    setProjectId(e.target.value ? parseInt(e.target.value) : null);
                    setSuiteId(null);
                    setSuiteMode("existing");
                    setSuiteName("");
                  }}
                  className="w-full px-3 py-2 border rounded-md text-sm bg-white"
                >
                  <option value="">Select a project...</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name} ({project.case_count} test cases)
                    </option>
                  ))}
                </select>
              </div>

              {selectedProject && (
                <>
                  {/* Suite Mode Toggle */}
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant={suiteMode === "existing" ? "default" : "outline"}
                      onClick={() => {
                        setSuiteMode("existing");
                        setSuiteName("");
                      }}
                      className="flex-1"
                      size="sm"
                    >
                      Select Existing Suite
                    </Button>
                    <Button
                      type="button"
                      variant={suiteMode === "new" ? "default" : "outline"}
                      onClick={() => {
                        setSuiteMode("new");
                        setSuiteId(null);
                      }}
                      className="flex-1"
                      size="sm"
                    >
                      <Plus className="h-3 w-3 mr-1" />
                      Create New Suite
                    </Button>
                  </div>

                  {suiteMode === "existing" && (
                    <div>
                      <Label htmlFor="suite-select">Suite *</Label>
                      <select
                        id="suite-select"
                        value={suiteId || ""}
                        onChange={(e) => setSuiteId(e.target.value ? parseInt(e.target.value) : null)}
                        className="w-full px-3 py-2 border rounded-md text-sm bg-white"
                      >
                        <option value="">Select a suite...</option>
                        {suites.map((suite) => (
                          <option key={suite.id} value={suite.id}>
                            {suite.name} ({suite.case_count} test cases)
                          </option>
                        ))}
                      </select>
                      {suites.length === 0 && (
                        <p className="text-xs text-gray-500 mt-1">
                          No suites found in "{selectedProject.name}". Create a new suite.
                        </p>
                      )}
                    </div>
                  )}

                  {suiteMode === "new" && (
                    <div>
                      <Label htmlFor="new-suite-name">New Suite Name *</Label>
                      <Input
                        id="new-suite-name"
                        placeholder="e.g., Checkout Flow, User Authentication"
                        value={suiteName}
                        onChange={(e) => setSuiteName(e.target.value)}
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Create a new suite within "{selectedProject.name}"
                      </p>
                    </div>
                  )}
                </>
              )}
            </>
          )}

          {/* New Project/Suite Creation */}
          {mode === "new" && (
            <>
              <div>
                <Label htmlFor="new-project-name">Project Name *</Label>
                <Input
                  id="new-project-name"
                  placeholder="e.g., E-Commerce, Mobile App"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="new-suite-name">Suite Name *</Label>
                <Input
                  id="new-suite-name"
                  placeholder="e.g., Checkout Flow, User Authentication"
                  value={suiteName}
                  onChange={(e) => setSuiteName(e.target.value)}
                />
              </div>
            </>
          )}

          {/* Test Cases Selection */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <Label>Select Test Cases ({selectedCount} of {totalCount})</Label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={toggleAll}
              >
                {selectedCount === totalCount ? "Deselect All" : "Select All"}
              </Button>
            </div>

            <div className="border rounded-md max-h-60 overflow-y-auto">
              {allTestCases.map((tc) => {
                const id = `${tc.type.charAt(0).toUpperCase()}-${tc.tc_id}`;
                const isSelected = selectedTestCases.has(id);

                return (
                  <label
                    key={id}
                    className={`flex items-start gap-3 p-3 border-b last:border-b-0 cursor-pointer hover:bg-gray-50 ${
                      isSelected ? "bg-blue-50" : ""
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleTestCase(id)}
                      className="mt-1"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm truncate">{tc.title}</span>
                        <Badge variant="outline" className="text-xs">
                          {tc.type}
                        </Badge>
                      </div>
                    </div>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Summary */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-blue-600 mt-0.5" />
              <div className="text-sm text-blue-700">
                <p className="font-medium">
                  {selectedCount} test case{selectedCount !== 1 ? "s" : ""} will be saved
                </p>
                {mode === "existing" ? (
                  <p className="text-xs mt-1">
                    To project: <strong>{selectedProject?.name || "..."}</strong>,
                    suite: <strong>
                      {suiteMode === "existing"
                        ? (suites.find((s) => s.id === suiteId)?.name || "...")
                        : (suiteName || "...")}
                    </strong>
                  </p>
                ) : (
                  <p className="text-xs mt-1">
                    New project: <strong>{projectName || "..."}</strong>,
                    new suite: <strong>{suiteName || "..."}</strong>
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={saving || selectedCount === 0}>
            {saving ? (
              <>Saving...</>
            ) : (
              <>
                <Check className="h-4 w-4 mr-2" />
                Save to Repository
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
