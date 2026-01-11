import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Cpu, Cloud, GitMerge, Info } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

type LLMMode = "local_only" | "glm_only" | "combined";

interface Props {
  llmMode: LLMMode;
  onLLMModeChange: (value: LLMMode) => void;
}

export default function LLMModeSelector({ llmMode, onLLMModeChange }: Props) {
  const modes = [
    {
      value: "local_only" as LLMMode,
      label: "Local LLM",
      icon: Cpu,
      description: "Use Ollama (offline)",
      detail: "Runs on your machine. No API costs. Models: llama3.1, mistral, etc.",
      speed: "Fast",
      quality: "Good",
      color: "bg-blue-50 border-blue-200",
      iconColor: "text-blue-500",
    },
    {
      value: "glm_only" as LLMMode,
      label: "GLM API",
      icon: Cloud,
      description: "Use Zhipu AI (online)",
      detail: "Cloud API with best quality. Requires API key. Model: glm-4.5-flash.",
      speed: "Medium",
      quality: "Excellent",
      color: "bg-purple-50 border-purple-200",
      iconColor: "text-purple-500",
    },
    {
      value: "combined" as LLMMode,
      label: "Combined",
      icon: GitMerge,
      description: "Both Local + GLM",
      detail: "Ensemble mode combining both for best results. 60% local, 40% GLM.",
      speed: "Slower",
      quality: "Best",
      color: "bg-green-50 border-green-200",
      iconColor: "text-green-500",
    },
  ];

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Cpu className="h-5 w-5 text-gray-700" />
            LLM Mode Selection
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            Choose which AI model to use for test generation
          </p>
        </div>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger>
              <Info className="h-4 w-4 text-gray-400" />
            </TooltipTrigger>
            <TooltipContent>
              <p className="max-w-xs text-xs">
                <strong>Local:</strong> Ollama running on your machine<br />
                <strong>GLM:</strong> Zhipu AI cloud API<br />
                <strong>Combined:</strong> Both models together
              </p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {modes.map((mode) => {
          const Icon = mode.icon;
          const isSelected = llmMode === mode.value;

          return (
            <button
              key={mode.value}
              onClick={() => onLLMModeChange(mode.value)}
              className={`
                relative p-4 rounded-lg border-2 text-left transition-all
                ${isSelected ? mode.color + " border-current" : "border-gray-200 hover:border-gray-300"}
              `}
            >
              <div className="flex items-start gap-3">
                <Icon className={`h-5 w-5 mt-0.5 ${isSelected ? mode.iconColor : "text-gray-400"}`} />
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Label className={`font-medium cursor-pointer ${isSelected ? mode.iconColor : ""}`}>
                      {mode.label}
                    </Label>
                    {isSelected && (
                      <Badge variant="secondary" className="text-xs">Active</Badge>
                    )}
                  </div>
                  <p className={`text-xs mb-2 ${isSelected ? "text-gray-700" : "text-gray-500"}`}>
                    {mode.description}
                  </p>
                  <div className="flex gap-2">
                    <Badge variant="outline" className="text-xs bg-white">
                      ⚡ {mode.speed}
                    </Badge>
                    <Badge variant="outline" className="text-xs bg-white">
                      ★ {mode.quality}
                    </Badge>
                  </div>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Info box */}
      <div className={`mt-4 p-3 rounded-lg text-sm ${
        llmMode === "local_only"
          ? "bg-blue-50 border border-blue-200"
          : llmMode === "glm_only"
          ? "bg-purple-50 border border-purple-200"
          : "bg-green-50 border border-green-200"
      }`}>
        <div className="flex items-start gap-2">
          <Info className={`h-4 w-4 mt-0.5 ${
            llmMode === "local_only"
              ? "text-blue-600"
              : llmMode === "glm_only"
              ? "text-purple-600"
              : "text-green-600"
          }`} />
          <div className="flex-1">
            {llmMode === "local_only" && (
              <p className="text-blue-700">
                <strong>Local LLM (Ollama):</strong> Runs entirely on your machine.
                Fast and free, but requires Ollama to be running. Good for privacy.
              </p>
            )}
            {llmMode === "glm_only" && (
              <p className="text-purple-700">
                <strong>GLM API (Zhipu AI):</strong> Cloud-based AI with excellent quality.
                Requires GLM_API_KEY in .env file. Best for complex requirements.
              </p>
            )}
            {llmMode === "combined" && (
              <p className="text-green-700">
                <strong>Combined Mode:</strong> Uses both local and GLM models together.
                Best quality results with ensemble learning. Takes longer but worth it for important test cases.
              </p>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
