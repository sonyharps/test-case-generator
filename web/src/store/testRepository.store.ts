// src/store/testRepository.store.ts
// Zustand store for Test Management / Repository

import { create } from "zustand";
import { persist } from "zustand/middleware";
import * as api from "@/api/testRepository";
import type {
  Project,
  TestSuite,
  RepositoryTestCase,
  ProjectCreate,
  ProjectUpdate,
  TestSuiteCreate,
  TestSuiteUpdate,
  RepositoryTestCaseCreate,
  RepositoryTestCaseUpdate,
  SaveToRepositoryRequest,
  TestCasesListParams,
  TestCaseType,
  Priority,
  AutomationStatus,
} from "@/api/testRepository";

// =====================================================
// Types for Store
// =====================================================

interface ProjectFilter {
  search?: string;
  is_active?: boolean;
}

interface TestCaseFilter extends Omit<TestCasesListParams, "page" | "page_size"> {
  page?: number;
  page_size?: number;
}

// =====================================================
// Store State
// =====================================================

interface TestRepositoryState {
  // Projects
  projects: Project[];
  selectedProjectId: number | null;
  projectsLoading: boolean;
  projectsError: string | null;

  // Suites
  suites: TestSuite[];
  selectedSuiteId: number | null;
  suitesLoading: boolean;
  suitesError: string | null;

  // Test Cases
  testCases: RepositoryTestCase[];
  selectedTestCaseId: number | null;
  testCasesLoading: boolean;
  testCasesError: string | null;
  testCasesTotal: number;
  testCasesFilter: TestCaseFilter;

  // UI State
  isCreatingProject: boolean;
  isCreatingSuite: boolean;
  isEditingSuite: boolean;
  editingSuiteId: number | null;
  isCreatingTestCase: boolean;
  isEditingTestCase: boolean;
  saveToRepositoryDialog: {
    open: boolean;
    orchestratorResult: any;
  };

  // Actions - Projects
  fetchProjects: (token: string) => Promise<void>;
  createProject: (data: ProjectCreate, token: string) => Promise<Project>;
  updateProject: (id: number, data: ProjectUpdate, token: string) => Promise<void>;
  deleteProject: (id: number, token: string) => Promise<void>;
  selectProject: (id: number | null) => void;

  // Actions - Suites
  fetchSuites: (projectId: number, token: string) => Promise<void>;
  createSuite: (data: Omit<TestSuiteCreate, "project_id">, token: string) => Promise<TestSuite>;
  updateSuite: (id: number, data: TestSuiteUpdate, token: string) => Promise<void>;
  deleteSuite: (id: number, token: string) => Promise<void>;
  selectSuite: (id: number | null) => void;
  setEditingSuite: (editing: boolean, suiteId?: number) => void;

  // Actions - Test Cases
  fetchTestCases: (token: string) => Promise<void>;
  createTestCase: (data: Omit<RepositoryTestCaseCreate, "suite_id">, token: string) => Promise<RepositoryTestCase>;
  updateTestCase: (id: number, data: RepositoryTestCaseUpdate, token: string) => Promise<void>;
  deleteTestCase: (id: number, token: string) => Promise<void>;
  selectTestCase: (id: number | null) => void;
  setTestCasesFilter: (filter: Partial<TestCaseFilter>) => void;
  clearTestCasesFilter: () => void;

  // Actions - Save from Orchestrator
  openSaveToRepositoryDialog: (orchestratorResult: any) => void;
  closeSaveToRepositoryDialog: () => void;
  saveFromOrchestrator: (data: SaveToRepositoryRequest, token: string) => Promise<void>;

  // UI Actions
  setCreatingProject: (value: boolean) => void;
  setCreatingSuite: (value: boolean) => void;
  setEditingSuite: (editing: boolean, suiteId?: number) => void;
  setCreatingTestCase: (value: boolean) => void;
  setEditingTestCase: (value: boolean) => void;

  // Reset
  reset: () => void;
}

const initialState = {
  projects: [],
  selectedProjectId: null,
  projectsLoading: false,
  projectsError: null,

  suites: [],
  selectedSuiteId: null,
  suitesLoading: false,
  suitesError: null,

  testCases: [],
  selectedTestCaseId: null,
  testCasesLoading: false,
  testCasesError: null,
  testCasesTotal: 0,
  testCasesFilter: {
    page: 1,
    page_size: 20,
  },

  isCreatingProject: false,
  isCreatingSuite: false,
  isEditingSuite: false,
  editingSuiteId: null,
  isCreatingTestCase: false,
  isEditingTestCase: false,
  saveToRepositoryDialog: {
    open: false,
    orchestratorResult: null,
  },
};

function reset() {
  return {
    ...initialState,
    testCasesFilter: {
      page: 1,
      page_size: 20,
    },
  };
}

// =====================================================
// Create Store
// =====================================================

export const useTestRepository = create<TestRepositoryState>()(
  persist(
    (set, get) => ({
      ...initialState,

      // =====================================================
      // Projects Actions
      // =====================================================

      fetchProjects: async (token: string) => {
        set({ projectsLoading: true, projectsError: null });
        try {
          const response = await api.listProjects(token);
          set({ projects: response.projects, projectsLoading: false });
        } catch (error: any) {
          set({ projectsError: error.message, projectsLoading: false });
        }
      },

      createProject: async (data: ProjectCreate, token: string) => {
        const project = await api.createProject(data, token);
        set((state) => ({ projects: [...state.projects, project] }));
        return project;
      },

      updateProject: async (id: number, data: ProjectUpdate, token: string) => {
        const updated = await api.updateProject(id, data, token);
        set((state) => ({
          projects: state.projects.map((p) => (p.id === id ? updated : p)),
        }));
      },

      deleteProject: async (id: number, token: string) => {
        await api.deleteProject(id, token);
        set((state) => ({
          projects: state.projects.filter((p) => p.id !== id),
          selectedProjectId: state.selectedProjectId === id ? null : state.selectedProjectId,
        }));
      },

      selectProject: (id: number | null) => {
        set({ selectedProjectId: id, selectedSuiteId: null, testCases: [], testCasesTotal: 0 });
      },

      // =====================================================
      // Suites Actions
      // =====================================================

      fetchSuites: async (projectId: number, token: string) => {
        set({ suitesLoading: true, suitesError: null });
        try {
          const response = await api.listSuites({ project_id: projectId }, token);
          set({ suites: response.suites, suitesLoading: false });
        } catch (error: any) {
          set({ suitesError: error.message, suitesLoading: false });
        }
      },

      createSuite: async (data: Omit<TestSuiteCreate, "project_id">, token: string) => {
        const { selectedProjectId } = get();
        if (!selectedProjectId) throw new Error("No project selected");

        const suite = await api.createSuite({ ...data, project_id: selectedProjectId }, token);
        set((state) => ({ suites: [...state.suites, suite] }));
        return suite;
      },

      updateSuite: async (id: number, data: TestSuiteUpdate, token: string) => {
        const updated = await api.updateSuite(id, data, token);
        set((state) => ({
          suites: state.suites.map((s) => (s.id === id ? updated : s)),
        }));
      },

      deleteSuite: async (id: number, token: string) => {
        await api.deleteSuite(id, token);
        set((state) => ({
          suites: state.suites.filter((s) => s.id !== id),
          selectedSuiteId: state.selectedSuiteId === id ? null : state.selectedSuiteId,
        }));
      },

      selectSuite: (id: number | null) => {
        set({
          selectedSuiteId: id,
          testCases: [],
          testCasesTotal: 0,
          testCasesFilter: {
            page: 1,
            page_size: 20,
            suite_id: id || undefined,
            project_id: get().selectedProjectId || undefined,
          },
        });
      },

      // =====================================================
      // Test Cases Actions
      // =====================================================

      fetchTestCases: async (token: string) => {
        set({ testCasesLoading: true, testCasesError: null });
        try {
          const filter = get().testCasesFilter;
          const response = await api.listTestCases(filter, token);
          set({ testCases: response.test_cases, testCasesTotal: response.total, testCasesLoading: false });
        } catch (error: any) {
          set({ testCasesError: error.message, testCasesLoading: false });
        }
      },

      createTestCase: async (data: Omit<RepositoryTestCaseCreate, "suite_id">, token: string) => {
        const { selectedSuiteId } = get();
        if (!selectedSuiteId) throw new Error("No suite selected");

        const testCase = await api.createTestCase({ ...data, suite_id: selectedSuiteId }, token);
        set((state) => ({ testCases: [...state.testCases, testCase] }));
        return testCase;
      },

      updateTestCase: async (id: number, data: RepositoryTestCaseUpdate, token: string) => {
        const updated = await api.updateTestCase(id, data, token);
        set((state) => ({
          testCases: state.testCases.map((tc) => (tc.id === id ? updated : tc)),
        }));
      },

      deleteTestCase: async (id: number, token: string) => {
        await api.deleteTestCase(id, token);
        set((state) => ({
          testCases: state.testCases.filter((tc) => tc.id !== id),
          selectedTestCaseId: state.selectedTestCaseId === id ? null : state.selectedTestCaseId,
        }));
      },

      selectTestCase: (id: number | null) => {
        set({ selectedTestCaseId: id });
      },

      setTestCasesFilter: (filter: Partial<TestCaseFilter>) => {
        set((state) => ({
          testCasesFilter: { ...state.testCasesFilter, ...filter },
        }));
      },

      clearTestCasesFilter: () => {
        set({
          testCasesFilter: {
            page: 1,
            page_size: 20,
            suite_id: get().selectedSuiteId || undefined,
            project_id: get().selectedProjectId || undefined,
          },
        });
      },

      // =====================================================
      // Save from Orchestrator
      // =====================================================

      openSaveToRepositoryDialog: (orchestratorResult: any) => {
        set({
          saveToRepositoryDialog: { open: true, orchestratorResult },
        });
      },

      closeSaveToRepositoryDialog: () => {
        set({
          saveToRepositoryDialog: { open: false, orchestratorResult: null },
        });
      },

      saveFromOrchestrator: async (data: SaveToRepositoryRequest, token: string) => {
        const result = await api.saveFromOrchestrator(data, token);

        // If created new project, select it
        if (data.project_name && result.project_id) {
          await get().fetchProjects(token);
          get().selectProject(result.project_id);
        }

        // If new suite was created or existing suite was used, select it and fetch test cases
        if (result.suite_id) {
          await get().fetchSuites(result.project_id, token);
          get().selectSuite(result.suite_id);
          // Fetch test cases for the selected suite
          await get().fetchTestCases(token);
        }

        return result;
      },

      // =====================================================
      // UI Actions
      // =====================================================

      setCreatingProject: (value: boolean) => set({ isCreatingProject: value }),
      setCreatingSuite: (value: boolean) => set({ isCreatingSuite: value }),
      setEditingSuite: (editing: boolean, suiteId?: number) => set({
        isEditingSuite: editing,
        editingSuiteId: suiteId ?? null,
      }),
      setCreatingTestCase: (value: boolean) => set({ isCreatingTestCase: value }),
      setEditingTestCase: (value: boolean) => set({ isEditingTestCase: value }),

      // =====================================================
      // Reset
      // =====================================================

      reset: () => set(reset()),
    }),
    {
      name: "test-repository-storage",
      partialize: (state) => ({
        selectedProjectId: state.selectedProjectId,
        selectedSuiteId: state.selectedSuiteId,
        testCasesFilter: state.testCasesFilter,
      }),
    }
  )
);
