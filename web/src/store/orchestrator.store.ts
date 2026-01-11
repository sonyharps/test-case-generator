import { create } from "zustand";
import { runOrchestrator, downloadOrchestratorPdf } from "@/api/orchestrator";
import type { OrchestratorResult } from "@/types/orchestrator";

type Provider = "local" | "groq";

interface State {
  requirement: string;
  model: string;
  provider: Provider;
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
  setProvider: (v: Provider) => void;
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
  model: "qwen3:1.7b",
  provider: "local" as Provider,
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
  setProvider: (v) => set({ provider: v }),
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
      provider,
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
      // Map provider to model for Groq
      let actualModel = model;
      if (provider === "groq") {
        // Map local model names to Groq equivalents
        const modelMap: Record<string, string> = {
          "qwen3:1.7b": "llama-3.1-8b-instant",
          "qwen2.5:7b": "llama-3.1-8b-instant",
          "llama3.1:8b": "llama-3.1-8b-instant",
          "qwen3:4b": "llama-3.3-70b-versatile",
          "mistral:7b": "mixtral-8x7b-32768",
        };
        actualModel = modelMap[model] || "llama-3.1-8b-instant";
      }

      const payload = {
        requirement,
        // Pass model directly for Local, or mapped model for Groq
        model: actualModel,
        generate_boundary: generateBoundary,
        include_risk_assessment: includeRisk,
        // Advanced RAG options
        use_rag: useRAG,
        use_advanced_rag: useAdvancedRAG,
        use_query_expansion: useQueryExpansion,
        use_reranking: useReranking,
        rag_top_k: ragTopK,
      };

      console.log("[Store] Sending payload:", { provider, model: actualModel, requirementLength: requirement.length });

      const res = await runOrchestrator(payload, token);

      console.log("[Store] Received response:", {
        hasResult: !!res,
        hasSummary: !!res?.summary,
        functionalCount: res?.functional?.length || 0,
        negativeCount: res?.negative?.length || 0,
        boundaryCount: res?.boundary?.length || 0,
      });

      set({ result: res });

      console.log("[Store] State updated with result");
    } catch (err: any) {
      console.error("[Store] Error running orchestrator:", err);
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
