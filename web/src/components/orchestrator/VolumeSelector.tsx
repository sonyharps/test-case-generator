// src/components/orchestrator/VolumeSelector.tsx
import { useOrchestrator } from "@/store/orchestrator.store";
import { cn } from "@/lib/utils";
import { Layers } from "lucide-react";

const OPTIONS = [
  {
    value: "standard" as const,
    label: "Standard",
    hint: "~90 test cases",
    sub: "28 F / 28 N / 24 B",
  },
  {
    value: "large" as const,
    label: "Large",
    hint: "~140 test cases",
    sub: "50 F / 50 N / 40 B",
  },
  {
    value: "max" as const,
    label: "Max",
    hint: "~200 test cases",
    sub: "70 F / 70 N / 60 B",
  },
];

export default function VolumeSelector() {
  const volume = useOrchestrator((s) => s.volume);
  const setVolume = useOrchestrator((s) => s.setVolume);

  return (
    <div className="bg-white shadow rounded-xl border border-gray-200 p-5">
      <div className="flex items-center gap-2 mb-1">
        <Layers className="h-5 w-5 text-indigo-600" />
        <h3 className="font-semibold text-gray-800">Test Case Volume</h3>
      </div>
      <p className="text-xs text-gray-500 mb-4">
        Jumlah minimum test case per kategori yang diminta dari LLM. Lebih banyak
        = lebih lama &amp; lebih banyak token.
      </p>
      <div className="grid grid-cols-3 gap-2">
        {OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setVolume(opt.value)}
            className={cn(
              "rounded-lg border p-3 text-left transition-colors",
              volume === opt.value
                ? "border-indigo-500 bg-indigo-50 ring-1 ring-indigo-500"
                : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
            )}
          >
            <div className="flex items-center justify-between">
              <span className="font-medium text-sm text-gray-900">
                {opt.label}
              </span>
              {volume === opt.value && (
                <span className="h-2 w-2 rounded-full bg-indigo-500" />
              )}
            </div>
            <div className="text-xs text-gray-600 mt-0.5">{opt.hint}</div>
            <div className="text-[11px] text-gray-400 mt-0.5">{opt.sub}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
