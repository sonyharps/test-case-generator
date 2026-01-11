import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Cpu, Loader2, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { useOrchestrator } from "@/store/orchestrator.store";
import { useAuth } from "@/store/auth.store";
import { fetchLLMModels } from "@/api/llm";

interface OllamaModel {
  id: string;
  name: string;
  description: string;
}

export default function OllamaModelSelector() {
  const { model, setModel } = useOrchestrator();
  const { accessToken } = useAuth();
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

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
            Choose a local Ollama model for test generation
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
          <span className="text-sm">Loading Ollama models...</span>
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
          <Label htmlFor="model-select">Select Model</Label>
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
            <div className="flex items-center gap-2 mt-2">
              <Badge variant="outline" className="text-xs bg-white">
                Selected: {models.find((m) => m.id === model)?.name || model}
              </Badge>
            </div>
          )}

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-3">
            <p className="text-sm text-blue-700">
              <strong>Local LLM (Ollama):</strong> Runs entirely on your machine.
              Fast and free. Make sure Ollama is running with <code>ollama serve</code>
            </p>
          </div>
        </div>
      )}
    </Card>
  );
}
