import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Globe, Loader2, RefreshCw, Cpu } from "lucide-react";
import { useEffect, useState } from "react";
import { useOrchestrator } from "@/store/orchestrator.store";

interface OpenRouterModel {
  id: string;
  name: string;
  description: string;
}

// Filename keeps the legacy "Ollama" name for continuity — since 2026-09 the
// app is OpenRouter-only and this lists curated OpenRouter models.

// Curated OpenRouter models suited for high-volume test-case generation.
// Requirement: large max output tokens (≥32k ideally) for ISO/IEC/IEEE 29119-3 suites.
// Benchmarked 2026-08 at Max volume (70/70/60 targets, doc id=13).
const OPENROUTER_MODELS: OpenRouterModel[] = [
  { id: "qwen/qwen3.7-flash", name: "Qwen3.7 Flash 🏆", description: "BEST VALUE — 205 TC / 2.3 min / $0.009" },
  { id: "google/gemini-2.5-flash", name: "Gemini 2.5 Flash ⚡", description: "FASTEST — 200 TC / 1.4 min" },
  { id: "openai/gpt-oss-120b", name: "GPT-OSS 120B", description: "Most token-efficient (294 tok/TC)" },
  { id: "qwen/qwen3-next-80b-a3b-instruct", name: "Qwen3 Next 80B 📦", description: "HIGHEST VOLUME — 249 TC" },
  { id: "deepseek/deepseek-v4-flash", name: "DeepSeek V4 Flash", description: "212 TC / $0.009" },
  { id: "z-ai/glm-5.2:free", name: "GLM 5.2 (Free)", description: "Free tier, rate-limited" },
];

export default function OllamaModelSelector() {
  const { model, setModel } = useOrchestrator();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // The list is static/curated — "loading" just validates the persisted
  // selection and falls back to the benchmark winner if it's stale.
  const loadModels = (showRefreshing = false) => {
    if (showRefreshing) setRefreshing(true);
    if (!OPENROUTER_MODELS.some((m) => m.id === model)) {
      setModel(OPENROUTER_MODELS[0].id);
    }
    setLoading(false);
    setRefreshing(false);
  };

  useEffect(() => {
    loadModels();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Cpu className="h-5 w-5 text-gray-700" />
            Model Selection
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            Pilih model OpenRouter untuk generate
          </p>
        </div>
        <button
          onClick={() => loadModels(true)}
          disabled={refreshing}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          title="Refresh models"
        >
          <RefreshCw className={`h-4 w-4 text-gray-500 ${refreshing ? "animate-spin" : ""}`} />
        </button>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-gray-500 py-4">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-sm">Loading models...</span>
        </div>
      ) : (
        <div className="space-y-3">
          <Label htmlFor="model-select">Model</Label>
          <select
            id="model-select"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-rose-500 focus:border-transparent"
          >
            {OPENROUTER_MODELS.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} ({m.id})
              </option>
            ))}
          </select>

          {model && (
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              <Badge variant="outline" className="text-xs bg-white">
                {OPENROUTER_MODELS.find((m) => m.id === model)?.name || model}
              </Badge>
              <Badge variant="outline" className="text-xs bg-rose-50">
                <Globe className="h-3 w-3 mr-1 inline" />
                Using: {model}
              </Badge>
            </div>
          )}

          <div className="bg-rose-50 border border-rose-200 rounded-lg p-3 mt-3">
            <p className="text-sm text-rose-700">
              <strong>OpenRouter:</strong> model dengan konteks/output besar (≥ 32k tokens)
              paling aman buat volume tinggi. Free-tier models bisa kena rate limit saat
              pipeline paralel.
            </p>
          </div>
        </div>
      )}
    </Card>
  );
}
