import { create } from "zustand";
import { runOrchestrator, downloadOrchestratorPdf } from "@/api/orchestrator";
import type { OrchestratorResult } from "@/types/orchestrator";

interface State {
  requirement: string;
  model: string;
  generateBoundary: boolean;
  includeRisk: boolean;

  loading: boolean;
  error?: string | null;
  result?: OrchestratorResult;

  setRequirement: (v: string) => void;
  setModel: (v: string) => void;
  setGenerateBoundary: (v: boolean) => void;
  setIncludeRisk: (v: boolean) => void;

  setLoading: (v: boolean) => void;
  setError: (e: string | null) => void;
  setResult: (r?: OrchestratorResult) => void;

  run: () => Promise<void>;
  downloadPdf: (req: string) => Promise<void>;
}

export const useOrchestrator = create<State>((set, get) => ({
  requirement: "",
  model: "llama3.1:8b",
  generateBoundary: true,
  includeRisk: true,

  loading: false,
  error: null,
  result: undefined,

  setRequirement: (v) => set({ requirement: v }),
  setModel: (v) => set({ model: v }),
  setGenerateBoundary: (v) => set({ generateBoundary: v }),
  setIncludeRisk: (v) => set({ includeRisk: v }),

  setLoading: (v) => set({ loading: v }),
  setError: (e) => set({ error: e }),
  setResult: (r) => set({ result: r }),

  run: async () => {
    const { requirement, model, generateBoundary, includeRisk } = get();

    if (!requirement.trim()) {
      set({ error: "Requirement cannot be empty." });
      return;
    }

    set({ loading: true, error: null });

    try {
      const payload = {
        requirement,
        model,
        generate_boundary: generateBoundary,
        include_risk_assessment: includeRisk,
      };

      const res = await runOrchestrator(payload);
      set({ result: res });
    } catch (err: any) {
      set({ error: err.message || "Failed to run orchestrator" });
    } finally {
      set({ loading: false });
    }
  },

  downloadPdf: async (req: string) => {
    set({ loading: true, error: null });
    try {
      const blob = await downloadOrchestratorPdf({ requirement: req });
      const url = window.URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = "orchestrator_report.pdf";
      a.click();

      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      set({ error: err.message || "PDF export failed" });
    } finally {
      set({ loading: false });
    }
  },
}));
