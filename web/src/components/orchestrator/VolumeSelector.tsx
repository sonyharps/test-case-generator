// src/components/orchestrator/VolumeSelector.tsx
import { useOrchestrator } from "@/store/orchestrator.store";
import { cn } from "@/lib/utils";
import { Layers, BookOpen } from "lucide-react";

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
  const useHistory = useOrchestrator((s) => s.useHistory);
  const setUseHistory = useOrchestrator((s) => s.setUseHistory);

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

      {/* RAG exemplar learning toggle */}
      <div className="mt-3 flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5">
        <div className="flex items-center gap-2.5">
          <BookOpen className="h-4 w-4 text-indigo-600" />
          <div>
            <div className="text-sm font-medium text-gray-900">
              Belajar dari riwayat
            </div>
            <div className="text-[11px] text-gray-500">
              Acuan gaya dari test case serupa yang pernah digenerate (RAG)
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setUseHistory(!useHistory)}
          className={cn(
            "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
            useHistory ? "bg-indigo-600" : "bg-gray-300"
          )}
          aria-label="Toggle belajar dari riwayat"
        >
          <span
            className={cn(
              "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
              useHistory ? "translate-x-6" : "translate-x-1"
            )}
          />
        </button>
      </div>
    </div>
  );
}
