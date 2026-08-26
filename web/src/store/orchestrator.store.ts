import { create } from "zustand";
import { persist } from "zustand/middleware";
import { runOrchestrator, downloadOrchestratorPdf, downloadOrchestratorExcel } from "@/api/orchestrator";
import type { OrchestratorResult } from "@/types/orchestrator";

type Provider = "local" | "groq" | "gemini" | "glm" | "openrouter";

interface State {
  requirement: string;
  model: string;
  provider: Provider;
  generateBoundary: boolean;
  includeRisk: boolean;

  // Document-driven generation (V8 pipeline) — multiple docs allowed for rich
  // mixed context (e.g. PRD + user stories + Figma flow in one generate).
  selectedDocumentIds: number[];

  // Advanced RAG options
  useRAG: boolean;
  useAdvancedRAG: boolean;
  useQueryExpansion: boolean;
  useReranking: boolean;
  ragTopK: number;

  /** TC volume preset — drives the per-category generation targets. */
  volume: "standard" | "large" | "max";

  loading: boolean;
  error?: string | null;
  result?: OrchestratorResult;

  setRequirement: (v: string) => void;
  setModel: (v: string) => void;
  setProvider: (v: Provider) => void;
  setGenerateBoundary: (v: boolean) => void;
  setIncludeRisk: (v: boolean) => void;
  setSelectedDocumentIds: (v: number[]) => void;
  toggleDocumentId: (id: number) => void;
  setVolume: (v: "standard" | "large" | "max") => void;

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
  downloadExcel: (token: string) => Promise<void>;
}

export const useOrchestrator = create<State>()(
  persist(
    (set, get) => ({
  requirement: "",
  model: "qwen3:1.7b",
  provider: "local" as Provider,
  generateBoundary: true,
  includeRisk: true,

  // V8 document-driven generation — empty array means legacy free-text (V7) mode
  selectedDocumentIds: [],

  // Advanced RAG defaults (all enabled by default)
  useRAG: true,
  useAdvancedRAG: true,
  useQueryExpansion: true,
  useReranking: true,
  ragTopK: 5,

  // Volume presets → backend `targets` (per-category minimums).
  // standard ≈ 90 TC | large ≈ 140 TC | max ≈ 200 TC (benchmark-proven safe)
  volume: "standard" as "standard" | "large" | "max",

  loading: false,
  error: null,
  result: undefined,

  setRequirement: (v) => set({ requirement: v }),
  setModel: (v) => set({ model: v }),
  setProvider: (v) => set({ provider: v }),
  setGenerateBoundary: (v) => set({ generateBoundary: v }),
  setIncludeRisk: (v) => set({ includeRisk: v }),
  setSelectedDocumentIds: (v) => set({ selectedDocumentIds: v }),
  toggleDocumentId: (id) =>
    set((state) => {
      const has = state.selectedDocumentIds.includes(id);
      return {
        selectedDocumentIds: has
          ? state.selectedDocumentIds.filter((d) => d !== id)
          : [...state.selectedDocumentIds, id],
      };
    }),
  setVolume: (v) => set({ volume: v }),

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
      selectedDocumentIds,
      useRAG,
      useAdvancedRAG,
      useQueryExpansion,
      useReranking,
      ragTopK,
      volume
    } = get();

    if (!requirement.trim() && selectedDocumentIds.length === 0) {
      set({ error: "Requirement cannot be empty." });
      return;
    }

    set({ loading: true, error: null });

    try {
      // Map provider to model for Groq and Gemini
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
      } else if (provider === "gemini") {
        // Map local model names to Gemini equivalents
        const modelMap: Record<string, string> = {
          "qwen3:1.7b": "gemini-2.0-flash-lite",
          "qwen2.5:7b": "gemini-2.0-flash-lite",
          "llama3.1:8b": "gemini-2.0-flash-lite",
          "qwen3:4b": "gemini-2.0-flash",
          "mistral:7b": "gemini-2.0-flash",
        };
        actualModel = modelMap[model] || "gemini-2.0-flash-lite";
      } else if (provider === "glm") {
        // GLM/Z.AI: glm-4.5-flash has the active quota on this account
        const modelMap: Record<string, string> = {
          "qwen3:1.7b": "glm-5-turbo",
          "qwen2.5:7b": "glm-5-turbo",
          "llama3.1:8b": "glm-5-turbo",
          "qwen3:4b": "glm-5-turbo",
          "mistral:7b": "glm-5-turbo",
        };
        actualModel = modelMap[model] || "glm-5-turbo";
      } else if (provider === "openrouter") {
        // OpenRouter models are already "vendor/model" — pass through.
        // Fallback to the benchmark value-winner if unset.
        actualModel = model.includes("/") ? model : "qwen/qwen3.7-flash";
      }

      // Volume preset → explicit per-category targets (backend volume knob)
      const VOLUME_TARGETS: Record<string, { functional: number; negative: number; boundary: number }> = {
        standard: { functional: 28, negative: 28, boundary: 24 },
        large: { functional: 50, negative: 50, boundary: 40 },
        max: { functional: 70, negative: 70, boundary: 60 },
      };

      const payload = {
        requirement: requirement || "(auto-derived from document)",
        // Pass model directly for Local, or mapped model for Groq
        model: actualModel,
        generate_boundary: generateBoundary,
        include_risk_assessment: includeRisk,
        targets: VOLUME_TARGETS[volume] ?? VOLUME_TARGETS.standard,
        // V8 document-driven generation: send document_ids when docs are picked
        ...(selectedDocumentIds.length > 0 ? { document_ids: selectedDocumentIds } : {}),
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

  downloadExcel: async (token: string) => {
    const { result, requirement, model } = get();
    if (!result) {
      set({ error: "Generate test cases first before exporting." });
      return;
    }
    set({ loading: true, error: null });
    try {
      // Send the full result so the export reflects exactly what the user sees
      const payload = {
        requirement,
        model,
        functional: result.functional || [],
        negative: result.negative || [],
        boundary: result.boundary || [],
        summary: result.summary || {},
        risk: result.risk || {},
        coverage_matrix: result.coverage_matrix || {},
        metadata: result.metadata || {},
      };
      const blob = await downloadOrchestratorExcel(payload, token);
      const url = window.URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = `test_cases_${new Date().toISOString().slice(0, 10)}.xlsx`;
      a.click();

      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      set({ error: err.message || "Excel export failed" });
    } finally {
      set({ loading: false });
    }
  },
}),
    {
      name: "orchestrator-storage",
      partialize: (state) => ({
        // Only persist these fields (exclude loading, error, result)
        requirement: state.requirement,
        model: state.model,
        provider: state.provider,
        generateBoundary: state.generateBoundary,
        includeRisk: state.includeRisk,
        selectedDocumentIds: state.selectedDocumentIds,
        useRAG: state.useRAG,
        useAdvancedRAG: state.useAdvancedRAG,
        useQueryExpansion: state.useQueryExpansion,
        useReranking: state.useReranking,
        ragTopK: state.ragTopK,
      }),
    }
  )
);
