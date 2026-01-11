import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Cpu, Zap, Info } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

type Provider = "local" | "groq";

interface Props {
  provider: Provider;
  onProviderChange: (value: Provider) => void;
}

export default function ProviderSelector({ provider, onProviderChange }: Props) {
  const providers = [
    {
      value: "local" as Provider,
      label: "Local",
      icon: Cpu,
      description: "Ollama (offline)",
      detail: "Runs on your machine. Free but slower. Models: qwen3, llama3.1, etc.",
      speed: "2-5 min",
      cost: "Free",
      color: "bg-blue-50 border-blue-200",
      iconColor: "text-blue-500",
    },
    {
      value: "groq" as Provider,
      label: "Groq Cloud",
      icon: Zap,
      description: "Fast cloud inference",
      detail: "Ultra-fast AI (8 calls in ~10 sec). Free tier: 8M tokens/day. Requires API key.",
      speed: "~10 sec",
      cost: "Free tier",
      color: "bg-orange-50 border-orange-200",
      iconColor: "text-orange-500",
    },
  ];

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Cpu className="h-5 w-5 text-gray-700" />
            AI Provider Selection
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            Choose where AI processing happens
          </p>
        </div>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger>
              <Info className="h-4 w-4 text-gray-400" />
            </TooltipTrigger>
            <TooltipContent>
              <p className="max-w-xs text-xs">
                <strong>Local:</strong> Ollama on your machine<br />
                <strong>Groq:</strong> Fast cloud AI (free tier available)
              </p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {providers.map((p) => {
          const Icon = p.icon;
          const isSelected = provider === p.value;

          return (
            <button
              key={p.value}
              onClick={() => onProviderChange(p.value)}
              className={`
                relative p-4 rounded-lg border-2 text-left transition-all
                ${isSelected ? p.color + " border-current" : "border-gray-200 hover:border-gray-300"}
              `}
            >
              <div className="flex items-start gap-3">
                <Icon className={`h-5 w-5 mt-0.5 ${isSelected ? p.iconColor : "text-gray-400"}`} />
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`font-medium ${isSelected ? p.iconColor : ""}`}>
                      {p.label}
                    </span>
                    {isSelected && (
                      <Badge variant="secondary" className="text-xs">Active</Badge>
                    )}
                  </div>
                  <p className={`text-xs mb-2 ${isSelected ? "text-gray-700" : "text-gray-500"}`}>
                    {p.description}
                  </p>
                  <div className="flex gap-2">
                    <Badge variant="outline" className="text-xs bg-white">
                      ⚡ {p.speed}
                    </Badge>
                    <Badge variant="outline" className="text-xs bg-white">
                      💰 {p.cost}
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
        provider === "local"
          ? "bg-blue-50 border border-blue-200"
          : "bg-orange-50 border border-orange-200"
      }`}>
        <div className="flex items-start gap-2">
          <Info className={`h-4 w-4 mt-0.5 ${
            provider === "local"
              ? "text-blue-600"
              : "text-orange-600"
          }`} />
          <div className="flex-1">
            {provider === "local" && (
              <p className="text-blue-700">
                <strong>Local (Ollama):</strong> Runs entirely on your machine.
                Slower but private. Make sure Ollama is running: <code>ollama serve</code>
              </p>
            )}
            {provider === "groq" && (
              <p className="text-orange-700">
                <strong>Groq Cloud:</strong> Ultra-fast inference (10x faster).
                Get free API key at <a href="https://console.groq.com/keys" target="_blank" rel="noopener noreferrer" className="underline">console.groq.com</a>
              </p>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
