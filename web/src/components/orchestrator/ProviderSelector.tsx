import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Globe, Info } from "lucide-react";

/**
 * OpenRouter is the one and only AI provider (2026-09 decision).
 * Kept as a component (not inlined into the page) so provider info
 * stays visible on the orchestrator form.
 */
export default function ProviderSelector() {
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Globe className="h-5 w-5 text-rose-500" />
            AI Provider
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            Where AI processing happens
          </p>
        </div>
        <Badge variant="secondary" className="bg-rose-50 text-rose-600 border border-rose-200">
          <Globe className="h-3 w-3 mr-1" />
          OpenRouter — Active
        </Badge>
      </div>

      {/* Info box */}
      <div className="p-3 rounded-lg text-sm bg-rose-50 border border-rose-200">
        <div className="flex items-start gap-2">
          <Info className="h-4 w-4 mt-0.5 text-rose-600" />
          <p className="text-rose-700 flex-1">
            <strong>OpenRouter:</strong> satu API key untuk 300+ model dari semua vendor
            (DeepSeek, Qwen, GPT, Claude, Gemini). Pay-per-use. Pilih model di dropdown
            bawah — pastikan max output ≥ 32k tokens buat volume tinggi. Get API key at{" "}
            <a href="https://openrouter.ai/keys" target="_blank" rel="noopener noreferrer" className="underline">openrouter.ai/keys</a>
          </p>
        </div>
      </div>
    </Card>
  );
}
