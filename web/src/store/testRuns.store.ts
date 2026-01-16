// src/store/testRuns.store.ts
// Zustand store for Test Runs Management

import { create } from "zustand";
import { persist } from "zustand/middleware";
import * as api from "@/api/testRepository";
import type {
  TestRun,
  TestRunWithResults,
  TestResult,
  TestRunCreate,
  TestResultUpdate,
  Milestone,
  MilestoneCreate,
} from "@/api/testRepository";
import { TestRunStatus, TestResultStatus } from "@/api/testRepository";

interface TestRunsState {
  // State
  testRuns: TestRun[];
  selectedTestRunId: number | null;
  selectedTestRun: TestRunWithResults | null;
  testRunsLoading: boolean;
  testRunsError: string | null;

  milestones: Milestone[];
  milestonesLoading: boolean;

  isCreatingRun: boolean;
  isCreatingMilestone: boolean;
  isExecutingRun: boolean;

  // Actions
  fetchTestRuns: (projectId: number, token: string) => Promise<void>;
  fetchTestRun: (testRunId: number, token: string) => Promise<void>;
  createTestRun: (data: TestRunCreate, token: string) => Promise<TestRun>;
  updateTestRun: (testRunId: number, data: { status?: TestRunStatus; name?: string }, token: string) => Promise<void>;
  deleteTestRun: (testRunId: number, token: string) => Promise<void>;
  cancelTestRun: (testRunId: number, token: string) => Promise<void>;
  selectTestRun: (id: number | null) => void;

  fetchMilestones: (projectId: number, token: string) => Promise<void>;
  createMilestone: (data: MilestoneCreate, token: string) => Promise<Milestone>;

  updateTestResult: (resultId: number, data: TestResultUpdate, token: string) => Promise<void>;
  bulkUpdateResults: (resultIds: number[], data: { status: TestResultStatus }, token: string) => Promise<void>;

  // UI Actions
  setCreatingRun: (value: boolean) => void;
  setCreatingMilestone: (value: boolean) => void;
  setExecutingRun: (value: boolean) => void;

  reset: () => void;
}

const initialState = {
  testRuns: [],
  selectedTestRunId: null,
  selectedTestRun: null,
  testRunsLoading: false,
  testRunsError: null,

  milestones: [],
  milestonesLoading: false,

  isCreatingRun: false,
  isCreatingMilestone: false,
  isExecutingRun: false,
};

function reset() {
  return {
    ...initialState,
  };
}

export const useTestRuns = create<TestRunsState>()(
  persist(
    (set, get) => ({
      ...initialState,

      // =====================================================
      // Test Runs Actions
      // =====================================================

      fetchTestRuns: async (projectId: number, token: string) => {
        set({ testRunsLoading: true, testRunsError: null });
        try {
          const response = await api.listTestRuns({ project_id: projectId }, token);
          set({ testRuns: response.test_runs, testRunsLoading: false });
        } catch (error: any) {
          set({ testRunsError: error.message, testRunsLoading: false });
        }
      },

      fetchTestRun: async (testRunId: number, token: string) => {
        set({ testRunsLoading: true, testRunsError: null });
        try {
          const testRun = await api.getTestRun(testRunId, token);
          set({ selectedTestRun: testRun, testRunsLoading: false });
        } catch (error: any) {
          set({ testRunsError: error.message, testRunsLoading: false });
        }
      },

      createTestRun: async (data: TestRunCreate, token: string) => {
        const testRun = await api.createTestRun(data, token);
        set((state) => ({ testRuns: [testRun, ...state.testRuns] }));
        return testRun;
      },

      updateTestRun: async (testRunId: number, data: { status?: TestRunStatus; name?: string }, token: string) => {
        const updated = await api.updateTestRun(testRunId, data, token);
        set((state) => ({
          testRuns: state.testRuns.map((tr) => (tr.id === testRunId ? updated : tr)),
          selectedTestRun: state.selectedTestRun?.id === testRunId
            ? { ...state.selectedTestRun, ...updated }
            : state.selectedTestRun,
        }));
      },

      deleteTestRun: async (testRunId: number, token: string) => {
        await api.deleteTestRun(testRunId, token);
        set((state) => ({
          testRuns: state.testRuns.filter((tr) => tr.id !== testRunId),
          selectedTestRunId: state.selectedTestRunId === testRunId ? null : state.selectedTestRunId,
          selectedTestRun: state.selectedTestRun?.id === testRunId ? null : state.selectedTestRun,
        }));
      },

      cancelTestRun: async (testRunId: number, token: string) => {
        const updated = await api.cancelTestRun(testRunId, token);
        set((state) => ({
          testRuns: state.testRuns.map((tr) => (tr.id === testRunId ? updated : tr)),
          selectedTestRun: state.selectedTestRun?.id === testRunId
            ? { ...state.selectedTestRun, status: updated.status }
            : state.selectedTestRun,
        }));
      },

      selectTestRun: (id: number | null) => {
        set({ selectedTestRunId: id, selectedTestRun: null });
      },

      // =====================================================
      // Milestones Actions
      // =====================================================

      fetchMilestones: async (projectId: number, token: string) => {
        set({ milestonesLoading: true });
        try {
          const response = await api.listMilestones(projectId, token);
          set({ milestones: response.milestones, milestonesLoading: false });
        } catch (error: any) {
          set({ milestonesLoading: false });
        }
      },

      createMilestone: async (data: MilestoneCreate, token: string) => {
        const milestone = await api.createMilestone(data, token);
        set((state) => ({ milestones: [...state.milestones, milestone] }));
        return milestone;
      },

      // =====================================================
      // Test Results Actions
      // =====================================================

      updateTestResult: async (resultId: number, data: TestResultUpdate, token: string) => {
        const updated = await api.updateTestResult(resultId, data, token);
        set((state) => {
          if (!state.selectedTestRun) return state;

          const updatedResults = state.selectedTestRun.test_results.map((r) =>
            r.id === resultId ? updated : r
          );

          // Recalculate progress
          const total = updatedResults.length;
          const passed = updatedResults.filter((r) => r.status === TestResultStatus.PASSED).length;
          const failed = updatedResults.filter((r) => r.status === TestResultStatus.FAILED).length;
          const blocked = updatedResults.filter((r) => r.status === TestResultStatus.BLOCKED).length;
          const skipped = updatedResults.filter((r) => r.status === TestResultStatus.SKIPPED).length;
          const pending = updatedResults.filter(
            (r) => r.status === TestResultStatus.PENDING || r.status === TestResultStatus.RETEST
          ).length;
          const passRate = total > 0 ? (passed / total) * 100 : 0;

          return {
            selectedTestRun: {
              ...state.selectedTestRun,
              test_results: updatedResults,
              progress: {
                total,
                passed,
                failed,
                blocked,
                skipped,
                pending,
                pass_rate: Math.round(passRate * 10) / 10,
              },
            },
          };
        });
      },

      bulkUpdateResults: async (resultIds: number[], data: { status: TestResultStatus }, token: string) => {
        await api.bulkUpdateTestResults(resultIds, data, token);

        // Update local state
        set((state) => {
          if (!state.selectedTestRun) return state;

          const updatedResults = state.selectedTestRun.test_results.map((r) =>
            resultIds.includes(r.id) ? { ...r, status: data.status || r.status } : r
          );

          const total = updatedResults.length;
          const passed = updatedResults.filter((r) => r.status === TestResultStatus.PASSED).length;
          const failed = updatedResults.filter((r) => r.status === TestResultStatus.FAILED).length;
          const blocked = updatedResults.filter((r) => r.status === TestResultStatus.BLOCKED).length;
          const skipped = updatedResults.filter((r) => r.status === TestResultStatus.SKIPPED).length;
          const pending = updatedResults.filter(
            (r) => r.status === TestResultStatus.PENDING || r.status === TestResultStatus.RETEST
          ).length;
          const passRate = total > 0 ? (passed / total) * 100 : 0;

          return {
            selectedTestRun: {
              ...state.selectedTestRun,
              test_results: updatedResults,
              progress: {
                total,
                passed,
                failed,
                blocked,
                skipped,
                pending,
                pass_rate: Math.round(passRate * 10) / 10,
              },
            },
          };
        });
      },

      // =====================================================
      // UI Actions
      // =====================================================

      setCreatingRun: (value: boolean) => set({ isCreatingRun: value }),
      setCreatingMilestone: (value: boolean) => set({ isCreatingMilestone: value }),
      setExecutingRun: (value: boolean) => set({ isExecutingRun: value }),

      // =====================================================
      // Reset
      // =====================================================

      reset: () => set(reset()),
    }),
    {
      name: "test-runs-storage",
      partialize: (state) => ({
        selectedTestRunId: state.selectedTestRunId,
      }),
    }
  )
);
