import { create } from "zustand";

interface TestCase {
  tc_id: string;
  title: string;
  preconditions?: string[];
  steps?: string[];
  expected_result?: string[];
}

interface OrchestratorState {
  loading: boolean;
  requirement: string;
  result: {
    summary?: string;
    functional?: TestCase[];
    negative?: TestCase[];
    boundary?: TestCase[];
    risk?: { level: string; notes: string[] };
    coverage_matrix?: {
      functional_count: number;
      negative_count: number;
      boundary_count: number;
    };
  } | null;

  setRequirement: (v: string) => void;
  orchestrate: () => Promise<void>;
}

export const useOrchestrator = create<OrchestratorState>((set, get) => ({
  loading: false,
  requirement: "",
  result: null,

  setRequirement: (v) => set({ requirement: v }),

  orchestrate: async () => {
    const requirement = get().requirement;
    if (!requirement) return;

    set({ loading: true });

    try {
      const res = await fetch("http://localhost:8000/v1/orchestrate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ requirement, model: "llama3.1:8b" }),
      });

      const data = await res.json();
      set({ result: data, loading: false });

    } catch (err) {
      console.error(err);
      set({ loading: false });
    }
  },
}));
