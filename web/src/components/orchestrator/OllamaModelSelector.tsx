import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Cpu, Loader2, RefreshCw, Zap, Sparkles, Cloud, Globe } from "lucide-react";
import { useEffect, useState } from "react";
import { useOrchestrator } from "@/store/orchestrator.store";
import { useAuth } from "@/store/auth.store";
import { fetchLLMModels } from "@/api/llm";

interface OllamaModel {
  id: string;
  name: string;
  description: string;
}

type Provider = "local" | "groq" | "gemini" | "glm" | "openrouter";

interface Props {
  provider: Provider;
}

// Curated OpenRouter models suited for high-volume test-case generation.
// Requirement: large max output tokens (≥32k ideally) for ISO/IEC/IEEE 29119-3 suites.
// Benchmarked 2026-08 at Max volume (70/70/60 targets, doc id=13).
const OPENROUTER_MODELS: OllamaModel[] = [
  { id: "qwen/qwen3.7-flash", name: "Qwen3.7 Flash 🏆", description: "BEST VALUE — 205 TC / 2.3 min / $0.009" },
  { id: "google/gemini-2.5-flash", name: "Gemini 2.5 Flash ⚡", description: "FASTEST — 200 TC / 1.4 min" },
  { id: "openai/gpt-oss-120b", name: "GPT-OSS 120B", description: "Most token-efficient (294 tok/TC)" },
  { id: "qwen/qwen3-next-80b-a3b-instruct", name: "Qwen3 Next 80B 📦", description: "HIGHEST VOLUME — 249 TC" },
  { id: "deepseek/deepseek-v4-flash", name: "DeepSeek V4 Flash", description: "212 TC / $0.009" },
  { id: "z-ai/glm-5.2:free", name: "GLM 5.2 (Free)", description: "Free tier, rate-limited" },
];

// Model mapping for cloud providers
const getModelMapping = (selectedModel: string, provider: Provider): string => {
  if (provider === "local") return selectedModel;

  if (provider === "openrouter") {
    // OpenRouter model ids already carry the vendor prefix — pass through.
    return selectedModel.includes("/") ? selectedModel : "deepseek/deepseek-chat";
  }

  if (provider === "groq") {
    const modelMap: Record<string, string> = {
      "qwen3:1.7b": "llama-3.1-8b-instant",
      "qwen2.5:7b": "llama-3.1-8b-instant",
      "llama3.1:8b": "llama-3.1-8b-instant",
      "qwen3:4b": "llama-3.3-70b-versatile",
      "mistral:7b": "mixtral-8x7b-32768",
    };
    return modelMap[selectedModel] || "llama-3.1-8b-instant";
  }

  if (provider === "gemini") {
    const modelMap: Record<string, string> = {
      "qwen3:1.7b": "gemini-2.0-flash-lite",
      "qwen2.5:7b": "gemini-2.0-flash-lite",
      "llama3.1:8b": "gemini-2.0-flash-lite",
      "qwen3:4b": "gemini-2.0-flash",
      "mistral:7b": "gemini-2.0-flash",
    };
    return modelMap[selectedModel] || "gemini-2.0-flash-lite";
  }

  if (provider === "glm") {
    const modelMap: Record<string, string> = {
      "qwen3:1.7b": "glm-5-turbo",
      "qwen2.5:7b": "glm-5-turbo",
      "llama3.1:8b": "glm-5-turbo",
      "qwen3:4b": "glm-5-turbo",
      "mistral:7b": "glm-5-turbo",
    };
    return modelMap[selectedModel] || "glm-5-turbo";
  }

  return selectedModel;
};

const getProviderInfo = (provider: Provider) => {
  switch (provider) {
    case "local":
      return {
        name: "Local (Ollama)",
        icon: Cpu,
        color: "blue",
        description: "Runs on your machine. Make sure Ollama is running.",
      };
    case "groq":
      return {
        name: "Groq Cloud",
        icon: Zap,
        color: "orange",
        description: "Ultra-fast cloud inference. Model is auto-mapped.",
      };
    case "gemini":
      return {
        name: "Gemini",
        icon: Sparkles,
        color: "purple",
        description: "Google Gemini 2.0 Flash. Model is auto-mapped.",
      };
    case "glm":
      return {
        name: "GLM (Z.AI)",
        icon: Cloud,
        color: "emerald",
        description: "Zhipu GLM-4.5-Air. Cost-effective cloud inference. Model is auto-mapped.",
      };
    case "openrouter":
      return {
        name: "OpenRouter",
        icon: Globe,
        color: "rose",
        description: "300+ models dari semua vendor via satu API key. Pay-per-use.",
      };
  }
};

export default function OllamaModelSelector({ provider }: Props) {
  const { model, setModel } = useOrchestrator();
  const { accessToken } = useAuth();
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const providerInfo = getProviderInfo(provider);
  const actualModel = getModelMapping(model, provider);
  const ProviderIcon = providerInfo.icon;

  const loadModels = async (showRefreshing = false) => {
    if (showRefreshing) setRefreshing(true);

    // OpenRouter: use the curated static list (no Ollama backend needed)
    if (provider === "openrouter") {
      setModels(OPENROUTER_MODELS);
      setError(null);
      if (!OPENROUTER_MODELS.some((m) => m.id === model)) {
        setModel(OPENROUTER_MODELS[0].id);
      }
      setLoading(false);
      setRefreshing(false);
      return;
    }

    try {
      const data = await fetchLLMModels(accessToken || undefined);
      const ollamaModels = data.ollama?.models || [];
      setModels(ollamaModels);
      setError(null);

      // Auto-select first model if none selected
      if (ollamaModels.length > 0 && !model) {
        setModel(ollamaModels[0].id);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load models");
      // Set default models as fallback
      setModels([
        { id: "llama3.1:8b", name: "Llama 3.1 8B", description: "General purpose, fast" },
        { id: "llama3.1:70b", name: "Llama 3.1 70B", description: "High quality, slower" },
        { id: "mistral:7b", name: "Mistral 7B", description: "Good balance" },
      ]);
    } finally {
      setLoading(false);
      if (showRefreshing) setRefreshing(false);
    }
  };

  useEffect(() => {
    if (provider === "openrouter") {
      loadModels();
    } else if (accessToken) {
      loadModels();
    }
  }, [accessToken, provider]);

  const handleRefresh = () => loadModels(true);

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Cpu className="h-5 w-5 text-gray-700" />
            Model Selection
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            {provider === "local"
              ? "Choose a local Ollama model"
              : `Select model quality - auto-mapped to ${providerInfo.name}`}
          </p>
        </div>
        <button
          onClick={handleRefresh}
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
      ) : error ? (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-3">
          <p className="text-sm text-yellow-700">{error}</p>
          <p className="text-xs text-yellow-600 mt-1">
            Make sure Ollama is running: <code>ollama serve</code>
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          <Label htmlFor="model-select">Model Quality</Label>
          <select
            id="model-select"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {models.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} ({m.id})
              </option>
            ))}
          </select>

          {model && (
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              <Badge variant="outline" className="text-xs bg-white">
                Base: {models.find((m) => m.id === model)?.name || model}
              </Badge>
              {provider !== "local" && (
                <Badge variant="outline" className={`text-xs bg-${providerInfo.color}-50`}>
                  <ProviderIcon className="h-3 w-3 mr-1 inline" />
                  Using: {actualModel}
                </Badge>
              )}
            </div>
          )}

          <div className={`bg-${providerInfo.color}-50 border border-${providerInfo.color}-200 rounded-lg p-3 mt-3`}>
            <p className={`text-sm text-${providerInfo.color}-700`}>
              <strong>{providerInfo.name}:</strong> {providerInfo.description}
              {provider !== "local" && ` Your selection is mapped to ${actualModel}.`}
            </p>
          </div>
        </div>
      )}
    </Card>
  );
}
