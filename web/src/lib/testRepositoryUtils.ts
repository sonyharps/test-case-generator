// src/lib/testRepositoryUtils.ts
// Utility functions for Test Management / Repository

import type { TestCaseType, Priority, AutomationStatus } from "@/api/testRepository";

// =====================================================
// Label Helpers
// =====================================================

export function TestCaseTypeLabel(type: TestCaseType): string {
  const labels: Record<TestCaseType, string> = {
    functional: "Functional",
    negative: "Negative",
    boundary: "Boundary",
    ui: "UI",
    api: "API",
    integration: "Integration",
    performance: "Performance",
    security: "Security",
    usability: "Usability",
    other: "Other",
  };
  return labels[type] || type;
}

export function PriorityLabel(priority: Priority): string {
  const labels: Record<Priority, string> = {
    critical: "Critical",
    high: "High",
    medium: "Medium",
    low: "Low",
  };
  return labels[priority] || priority;
}

export function AutomationStatusLabel(status: AutomationStatus): string {
  const labels: Record<AutomationStatus, string> = {
    automated: "Automated",
    manual: "Manual",
    to_be_automated: "To Automate",
    none: "None",
  };
  return labels[status] || status;
}

// =====================================================
// Color Helpers
// =====================================================

export function PriorityColor(priority: Priority): string {
  const colors: Record<Priority, string> = {
    critical: "bg-red-100 text-red-700 border-red-200",
    high: "bg-orange-100 text-orange-700 border-orange-200",
    medium: "bg-yellow-100 text-yellow-700 border-yellow-200",
    low: "bg-gray-100 text-gray-700 border-gray-200",
  };
  return colors[priority] || "bg-gray-100 text-gray-700";
}

export function TestCaseTypeColor(type: TestCaseType): string {
  const colors: Record<TestCaseType, string> = {
    functional: "bg-blue-100 text-blue-700 border-blue-200",
    negative: "bg-red-100 text-red-700 border-red-200",
    boundary: "bg-purple-100 text-purple-700 border-purple-200",
    ui: "bg-pink-100 text-pink-700 border-pink-200",
    api: "bg-green-100 text-green-700 border-green-200",
    integration: "bg-indigo-100 text-indigo-700 border-indigo-200",
    performance: "bg-yellow-100 text-yellow-700 border-yellow-200",
    security: "bg-red-100 text-red-700 border-red-200",
    usability: "bg-teal-100 text-teal-700 border-teal-200",
    other: "bg-gray-100 text-gray-700 border-gray-200",
  };
  return colors[type] || "bg-gray-100 text-gray-700";
}

// =====================================================
// Conversion Helpers
// =====================================================

/**
 * Convert orchestrator test case to repository test case format
 */
export function orchestratorToRepositoryTestCase(
  orchestratorTC: any,
  tcType: TestCaseType = TestCaseType.FUNCTIONAL
) {
  return {
    title: orchestratorTC.title,
    description: orchestratorTC.description || "",
    tc_type: tcType,
    priority: "medium" as Priority,
    automation_status: "manual" as AutomationStatus,
    preconditions: Array.isArray(orchestratorTC.preconditions)
      ? orchestratorTC.preconditions
      : [],
    steps: Array.isArray(orchestratorTC.steps)
      ? orchestratorTC.steps.map((step: string, index: number) => ({
          step: index + 1,
          action: step,
          expected: Array.isArray(orchestratorTC.expected_result)
            ? orchestratorTC.expected_result[index] || ""
            : "",
        }))
      : [],
    expected_result: Array.isArray(orchestratorTC.expected_result)
      ? orchestratorTC.expected_result.join("\n")
      : orchestratorTC.expected_result || "",
    tags: [],
  };
}
