import { create } from "zustand";
import { runOrchestrator, downloadOrchestratorPdf } from "@/api/orchestrator";
import type { OrchestratorResult } from "@/types/orchestrator";

interface State {
  requirement: string;
  model: string;
  generateBoundary: boolean;
  includeRisk: boolean;

  // Advanced RAG options
  useRAG: boolean;
  useAdvancedRAG: boolean;
  useQueryExpansion: boolean;
  useReranking: boolean;
  ragTopK: number;

  loading: boolean;
  error?: string | null;
  result?: OrchestratorResult;

  setRequirement: (v: string) => void;
  setModel: (v: string) => void;
  setGenerateBoundary: (v: boolean) => void;
  setIncludeRisk: (v: boolean) => void;

  // Advanced RAG setters
  setUseRAG: (v: boolean) => void;
  setUseAdvancedRAG: (v: boolean) => void;
  setUseQueryExpansion: (v: boolean) => void;
  setUseReranking: (v: boolean) => void;
  setRagTopK: (v: number) => void;

  setLoading: (v: boolean) => void;
  setError: (e: string | null) => void;
  setResult: (r?: OrchestratorResult) => void;

  run: (token: string) => Promise<void>;
  downloadPdf: (req: string, token: string) => Promise<void>;
}

export const useOrchestrator = create<State>((set, get) => ({
  requirement: "",
  model: "llama3.1:8b",
  generateBoundary: true,
  includeRisk: true,

  // Advanced RAG defaults (all enabled by default)
  useRAG: true,
  useAdvancedRAG: true,
  useQueryExpansion: true,
  useReranking: true,
  ragTopK: 5,

  loading: false,
  error: null,
  result: undefined,

  setRequirement: (v) => set({ requirement: v }),
  setModel: (v) => set({ model: v }),
  setGenerateBoundary: (v) => set({ generateBoundary: v }),
  setIncludeRisk: (v) => set({ includeRisk: v }),

  // Advanced RAG setters
  setUseRAG: (v) => set({ useRAG: v }),
  setUseAdvancedRAG: (v) => set({ useAdvancedRAG: v }),
  setUseQueryExpansion: (v) => set({ useQueryExpansion: v }),
  setUseReranking: (v) => set({ useReranking: v }),
  setRagTopK: (v) => set({ ragTopK: v }),

  setLoading: (v) => set({ loading: v }),
  setError: (e) => set({ error: e }),
  setResult: (r) => set({ result: r }),

  run: async (token: string) => {
    const {
      requirement,
      model,
      generateBoundary,
      includeRisk,
      useRAG,
      useAdvancedRAG,
      useQueryExpansion,
      useReranking,
      ragTopK
    } = get();

    if (!requirement.trim()) {
      set({ error: "Requirement cannot be empty." });
      return;
    }

    set({ loading: true, error: null });

    try {
      const payload = {
        requirement,
        provider: "ollama",  // or make this configurable
        model,
        generate_boundary: generateBoundary,
        include_risk: includeRisk,
        // Advanced RAG options
        use_rag: useRAG,
        use_advanced_rag: useAdvancedRAG,
        use_query_expansion: useQueryExpansion,
        use_reranking: useReranking,
        rag_top_k: ragTopK,
      };

      const res = await runOrchestrator(payload, token);
      set({ result: res });
    } catch (err: any) {
      set({ error: err.message || "Failed to run orchestrator" });
    } finally {
      set({ loading: false });
    }
  },

  downloadPdf: async (req: string, token: string) => {
    set({ loading: true, error: null });
    try {
      const blob = await downloadOrchestratorPdf({ requirement: req }, token);
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
