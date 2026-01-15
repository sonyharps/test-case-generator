import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Cpu, Loader2, RefreshCw, Zap, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { useOrchestrator } from "@/store/orchestrator.store";
import { useAuth } from "@/store/auth.store";
import { fetchLLMModels } from "@/api/llm";

interface OllamaModel {
  id: string;
  name: string;
  description: string;
}

type Provider = "local" | "groq" | "gemini";

interface Props {
  provider: Provider;
}

// Model mapping for cloud providers
const getModelMapping = (selectedModel: string, provider: Provider): string => {
  if (provider === "local") return selectedModel;

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
    if (accessToken) {
      loadModels();
    }
  }, [accessToken]);

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
