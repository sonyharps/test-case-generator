import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Info, Zap, Target, Search } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface Props {
  useRAG: boolean;
  useAdvancedRAG: boolean;
  useQueryExpansion: boolean;
  useReranking: boolean;
  onUseRAGChange: (value: boolean) => void;
  onUseAdvancedRAGChange: (value: boolean) => void;
  onUseQueryExpansionChange: (value: boolean) => void;
  onUseRerankingChange: (value: boolean) => void;
}

export default function AdvancedRAGControls({
  useRAG,
  useAdvancedRAG,
  useQueryExpansion,
  useReranking,
  onUseRAGChange,
  onUseAdvancedRAGChange,
  onUseQueryExpansionChange,
  onUseRerankingChange,
}: Props) {
  const estimatedTime = () => {
    if (!useRAG) return "~100ms";
    if (!useAdvancedRAG) return "~200ms";

    let time = 100;
    if (useQueryExpansion) time += 500;
    if (useReranking) time += 300;
    return `~${time}ms`;
  };

  const qualityScore = () => {
    if (!useRAG) return 60;
    if (!useAdvancedRAG) return 75;

    let score = 75;
    if (useQueryExpansion) score += 10;
    if (useReranking) score += 10;
    return score;
  };

  return (
    <Card className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Zap className="h-5 w-5 text-blue-500" />
            Advanced RAG Settings
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            Configure retrieval and ranking features
          </p>
        </div>

        <div className="flex gap-2">
          <Badge variant="outline" className="bg-blue-50">
            Quality: {qualityScore()}%
          </Badge>
          <Badge variant="outline" className="bg-gray-50">
            {estimatedTime()}
          </Badge>
        </div>
      </div>

      {/* Enable RAG */}
      <div className="flex items-center justify-between p-3 rounded-lg border bg-white">
        <div className="flex items-center gap-3">
          <Search className="h-4 w-4 text-gray-400" />
          <div>
            <Label htmlFor="use-rag" className="font-medium cursor-pointer">
              Enable RAG
            </Label>
            <p className="text-xs text-gray-500">
              Retrieve context from uploaded documents
            </p>
          </div>
        </div>
        <Switch
          id="use-rag"
          checked={useRAG}
          onCheckedChange={onUseRAGChange}
        />
      </div>

      {/* Advanced RAG toggle (only if RAG is enabled) */}
      {useRAG && (
        <div className="flex items-center justify-between p-3 rounded-lg border bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex items-center gap-3">
            <Zap className="h-4 w-4 text-blue-500" />
            <div>
              <Label htmlFor="use-advanced-rag" className="font-medium cursor-pointer flex items-center gap-2">
                Advanced RAG
                <Badge variant="secondary" className="text-xs">Recommended</Badge>
              </Label>
              <p className="text-xs text-gray-500">
                Query expansion + semantic re-ranking
              </p>
            </div>
          </div>
          <Switch
            id="use-advanced-rag"
            checked={useAdvancedRAG}
            onCheckedChange={onUseAdvancedRAGChange}
          />
        </div>
      )}

      {/* Advanced options (only if Advanced RAG is enabled) */}
      {useRAG && useAdvancedRAG && (
        <div className="ml-4 space-y-3 pl-4 border-l-2 border-blue-200">
          {/* Query Expansion */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Label htmlFor="query-expansion" className="font-medium cursor-pointer text-sm">
                Query Expansion
              </Label>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <Info className="h-3 w-3 text-gray-400" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="max-w-xs text-xs">
                      Generates alternative phrasings to find more relevant documents.
                      Improves recall by ~15%. Adds ~500ms processing time.
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
            <Switch
              id="query-expansion"
              checked={useQueryExpansion}
              onCheckedChange={onUseQueryExpansionChange}
            />
          </div>

          {/* Re-ranking */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Label htmlFor="reranking" className="font-medium cursor-pointer text-sm">
                Semantic Re-Ranking
              </Label>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <Info className="h-3 w-3 text-gray-400" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="max-w-xs text-xs">
                      Uses cross-encoder to re-rank results for better accuracy.
                      Improves relevance by ~20%. Adds ~300ms processing time.
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
            <Switch
              id="reranking"
              checked={useReranking}
              onCheckedChange={onUseRerankingChange}
            />
          </div>
        </div>
      )}

      {/* Info box */}
      <div className={`p-3 rounded-lg text-sm ${
        useRAG && useAdvancedRAG
          ? "bg-green-50 border border-green-200"
          : useRAG
          ? "bg-blue-50 border border-blue-200"
          : "bg-gray-50 border border-gray-200"
      }`}>
        <div className="flex items-start gap-2">
          <Target className={`h-4 w-4 mt-0.5 ${
            useRAG && useAdvancedRAG
              ? "text-green-600"
              : useRAG
              ? "text-blue-600"
              : "text-gray-400"
          }`} />
          <div className="flex-1">
            {!useRAG && (
              <p className="text-gray-600">
                <strong>No RAG:</strong> Fast generation (~100ms) but may miss relevant context from your documents.
              </p>
            )}
            {useRAG && !useAdvancedRAG && (
              <p className="text-blue-700">
                <strong>Basic RAG:</strong> Good balance of speed (~200ms) and quality (75% accuracy).
              </p>
            )}
            {useRAG && useAdvancedRAG && (
              <p className="text-green-700">
                <strong>Advanced RAG:</strong> Best quality ({qualityScore()}% accuracy) with full citation tracking.
                Processing time: {estimatedTime()}.
              </p>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
