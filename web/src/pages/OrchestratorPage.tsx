// src/pages/OrchestratorPage.tsx
// Wizard 3 langkah (implementasi mockup UX penyederhanaan 2026-09):
//   1. Sumber  — pilih dokumen / tulis requirement
//   2. Jumlah  — preset volume + pengaturan lanjutan (collapsed)
//   3. Hasil   — progress bertahap → hasil + export/Drive
import { useEffect, useState } from "react";
import SummaryCard from "@/components/orchestrator/SummaryCard";
import TestCaseTabs from "@/components/orchestrator/TestCaseTabs";
import RiskCard from "@/components/orchestrator/RiskCard";
import CoverageCard from "@/components/orchestrator/CoverageCard";
import AdvancedRAGControls from "@/components/orchestrator/AdvancedRAGControls";
import CitationsCard from "@/components/orchestrator/CitationsCard";
import OllamaModelSelector from "@/components/orchestrator/OllamaModelSelector";
import ProviderSelector from "@/components/orchestrator/ProviderSelector";
import DocumentPicker from "@/components/orchestrator/DocumentPicker";
import VolumeSelector from "@/components/orchestrator/VolumeSelector";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, FileSpreadsheet, Cloud, ExternalLink, Check, ArrowLeft, ArrowRight, AlertCircle } from "lucide-react";
import { useAuth } from "@/store/auth.store";
import { useOrchestrator } from "@/store/orchestrator.store";
import { normalizeSummary } from "@/lib/normalizers/normalizeSummary";
import { cn } from "@/lib/utils";

const STEPS = ["Sumber", "Jumlah", "Hasil"] as const;

/* ---------- Stepper ---------- */
function WizardStepper({ step }: { step: number }) {
  return (
    <div className="flex items-center">
      {STEPS.map((label, i) => {
        const n = i + 1;
        const active = step === n;
        const done = step > n;
        return (
          <div key={label} className={cn("flex items-center", i > 0 && "flex-1")}>
            {i > 0 && (
              <div
                className={cn(
                  "flex-1 h-px mx-3 min-w-6",
                  step > i ? "bg-slate-900" : "bg-slate-200"
                )}
              />
            )}
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  "h-7 w-7 rounded-full flex items-center justify-center text-xs font-semibold border",
                  done && "bg-slate-900 text-white border-slate-900",
                  active && "bg-white text-slate-900 border-slate-900 ring-4 ring-slate-100",
                  !done && !active && "bg-white text-slate-400 border-slate-200"
                )}
              >
                {done ? <Check className="h-3.5 w-3.5" /> : n}
              </div>
              <span
                className={cn(
                  "text-sm",
                  active ? "font-semibold text-slate-900" : "text-slate-400"
                )}
              >
                {label}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ---------- Langkah 3: progress bertahap (estimasi dari benchmark) ---------- */
const STAGES = [
  { label: "Membaca & memahami dokumen", until: 12 },
  { label: "Mencari test case serupa di riwayat", until: 25 },
  { label: "Menyusun test case fungsional", until: 70 },
  { label: "Menyusun test case negatif & boundary", until: 115 },
  { label: "Analisis risiko & coverage", until: 160 },
];

function GenerateProgress({ docCount }: { docCount: number }) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(t);
  }, []);

  const activeIdx = STAGES.findIndex((s) => elapsed < s.until);
  const stageIdx = activeIdx === -1 ? STAGES.length - 1 : activeIdx;
  const pct = Math.min(95, Math.round((elapsed / 150) * 100));

  return (
    <Card>
      <CardContent className="p-6 space-y-4">
        <div className="flex items-center gap-3">
          <Loader2 className="h-5 w-5 animate-spin text-slate-700" />
          <div>
            <h3 className="font-semibold text-slate-800">
              Sedang menyusun test case
            </h3>
            <p className="text-xs text-slate-500">
              {docCount > 0
                ? `Membaca ${docCount} dokumen · `
                : ""}
              Estimasi ±1–3 menit (dari data benchmark)
            </p>
          </div>
        </div>

        <div className="space-y-2">
          <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-slate-900 transition-all duration-1000"
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className="text-[11px] text-slate-400">{pct}%</p>
        </div>

        <div className="space-y-2 pt-1">
          {STAGES.map((s, i) => (
            <div
              key={s.label}
              className={cn(
                "flex items-center gap-2.5 text-sm",
                i < stageIdx && "text-slate-500",
                i === stageIdx && "text-slate-900 font-medium",
                i > stageIdx && "text-slate-300"
              )}
            >
              <div
                className={cn(
                  "h-5 w-5 rounded-full flex items-center justify-center text-[10px] border shrink-0",
                  i < stageIdx && "bg-slate-900 text-white border-slate-900",
                  i === stageIdx && "border-slate-900 text-slate-900",
                  i > stageIdx && "border-slate-200 text-slate-300"
                )}
              >
                {i < stageIdx ? <Check className="h-3 w-3" /> : i + 1}
              </div>
              {s.label}
              {i === stageIdx && <Loader2 className="h-3.5 w-3.5 animate-spin text-slate-400" />}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/* ---------- Halaman utama ---------- */
export default function OrchestratorPage() {
  const {
    result,
    loading,
    error,
    requirement,
    setRequirement,
    selectedDocumentIds,
    useRAG,
    useAdvancedRAG,
    useQueryExpansion,
    useReranking,
    setUseRAG,
    setUseAdvancedRAG,
    setUseQueryExpansion,
    setUseReranking,
    run,
    downloadExcel,
    saveToDrive,
    driveState,
  } = useOrchestrator();
  const accessToken = useAuth((s) => s.accessToken);

  const [step, setStep] = useState(1);
  const [sourceTab, setSourceTab] = useState<"dokumen" | "tulis">("dokumen");

  const canProceed =
    requirement.trim().length > 0 || selectedDocumentIds.length > 0;

  const handleStart = () => {
    setStep(3);
    if (accessToken) run(accessToken);
  };

  const handleExportExcel = () => {
    if (accessToken) downloadExcel(accessToken);
  };

  const handleSaveToDrive = () => {
    if (accessToken) saveToDrive(accessToken);
  };

  return (
    <div className="space-y-6">
      <WizardStepper step={step} />

      {/* ================= LANGKAH 1: SUMBER ================= */}
      {step === 1 && (
        <Card>
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold text-slate-900">
              Mau ditest dari mana?
            </h2>
            <p className="text-sm text-slate-500 mt-0.5 mb-4">
              Pilih dokumen yang sudah diupload, atau tulis langsung
              requirement-nya.
            </p>

            <div className="flex gap-1 rounded-lg bg-slate-100 p-1 w-fit mb-4">
              <button
                onClick={() => setSourceTab("dokumen")}
                className={cn(
                  "px-4 py-1.5 rounded-md text-sm font-medium transition-colors",
                  sourceTab === "dokumen"
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-500 hover:text-slate-700"
                )}
              >
                Pilih Dokumen
              </button>
              <button
                onClick={() => setSourceTab("tulis")}
                className={cn(
                  "px-4 py-1.5 rounded-md text-sm font-medium transition-colors",
                  sourceTab === "tulis"
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-500 hover:text-slate-700"
                )}
              >
                Tulis Requirement
              </button>
            </div>

            {sourceTab === "dokumen" ? (
              <div className="space-y-3">
                <DocumentPicker />
                <div className="rounded-lg bg-slate-50 border border-slate-200 px-3.5 py-2.5 text-sm text-slate-600">
                  Bisa memilih <strong>lebih dari satu</strong> dokumen — AI
                  akan menggabungkan isinya (misal PRD + user story). Belum ada
                  dokumennya? Upload dulu di menu <strong>Dokumen</strong>.
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <textarea
                  value={requirement}
                  onChange={(e) => setRequirement(e.target.value)}
                  className="w-full min-h-40 border border-slate-300 rounded-lg p-3.5 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                  placeholder={
                    "Contoh: Fitur transfer antar bank via QRIS\n\n1. User scan QR merchant\n2. Sistem menampilkan nominal & nama merchant\n3. User konfirmasi dengan PIN\n4. Transaksi sukses → notifikasi + struk"
                  }
                />
                <div className="rounded-lg bg-slate-50 border border-slate-200 px-3.5 py-2.5 text-sm text-slate-600">
                  Tulis poin-poinnya saja, tidak harus formal — AI yang akan
                  menyusunnya menjadi test case lengkap (langkah, expected
                  result, prioritas).
                </div>
              </div>
            )}

            <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs text-slate-400">
                {canProceed
                  ? selectedDocumentIds.length > 0
                    ? `${selectedDocumentIds.length} dokumen dipilih`
                    : "Requirement terisi"
                  : "Pilih minimal 1 dokumen atau tulis requirement"}
              </span>
              <Button onClick={() => setStep(2)} disabled={!canProceed}>
                Lanjut ke Jumlah <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ================= LANGKAH 2: JUMLAH ================= */}
      {step === 2 && (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              Mau seberapa banyak?
            </h2>
            <p className="text-sm text-slate-500 mt-0.5">
              Angka berdasarkan hasil benchmark nyata. Bisa diubah kapan saja.
            </p>
          </div>

          <VolumeSelector />

          {/* Pengaturan lanjatan — hidden by default, default sudah optimal */}
          <details className="group rounded-xl border border-slate-200 bg-white shadow-sm">
            <summary className="px-5 py-3.5 text-sm font-medium text-slate-500 cursor-pointer select-none list-none flex items-center justify-between">
              <span>
                Pengaturan lanjutan
                <span className="ml-2 font-normal text-slate-400">
                  (tidak perlu diubah — sudah optimal)
                </span>
              </span>
              <span className="text-slate-400 group-open:rotate-180 transition-transform">▾</span>
            </summary>
            <div className="px-5 pb-5 pt-1 space-y-4 border-t border-slate-100">
              <ProviderSelector />
              <OllamaModelSelector />
              <AdvancedRAGControls
                useRAG={useRAG}
                useAdvancedRAG={useAdvancedRAG}
                useQueryExpansion={useQueryExpansion}
                useReranking={useReranking}
                onUseRAGChange={setUseRAG}
                onUseAdvancedRAGChange={setUseAdvancedRAG}
                onUseQueryExpansionChange={setUseQueryExpansion}
                onUseRerankingChange={setUseReranking}
              />
            </div>
          </details>

          <div className="flex items-center justify-between pt-1">
            <Button variant="outline" onClick={() => setStep(1)}>
              <ArrowLeft className="h-4 w-4 mr-1" /> Kembali
            </Button>
            <Button onClick={handleStart} disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Memproses...
                </>
              ) : (
                "Mulai Generate"
              )}
            </Button>
          </div>
        </div>
      )}

      {/* ================= LANGKAH 3: HASIL ================= */}
      {step === 3 && (
        <div className="space-y-5">
          {loading && <GenerateProgress docCount={selectedDocumentIds.length} />}

          {!loading && error && (
            <Card>
              <CardContent className="p-6">
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-slate-900">
                      Generate gagal
                    </h3>
                    <p className="text-sm text-slate-500 mt-1">{error}</p>
                  </div>
                </div>
                <div className="mt-4 flex gap-2">
                  <Button variant="outline" onClick={() => setStep(2)}>
                    <ArrowLeft className="h-4 w-4 mr-1" /> Ubah pengaturan
                  </Button>
                  <Button onClick={handleStart}>Coba lagi</Button>
                </div>
              </CardContent>
            </Card>
          )}

          {!loading && !error && !result && (
            <Card>
              <CardContent className="p-6 text-center text-sm text-slate-500">
                Belum ada hasil.{" "}
                <button
                  className="text-slate-900 underline font-medium"
                  onClick={() => setStep(2)}
                >
                  Kembali ke langkah Jumlah
                </button>{" "}
                untuk memulai generate.
              </CardContent>
            </Card>
          )}

          {result && (
            <>
              {/* Export actions */}
              <div className="flex items-center gap-2 flex-wrap">
                <button
                  onClick={handleExportExcel}
                  disabled={loading}
                  className="inline-flex items-center gap-2 rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-emerald-700 disabled:opacity-50"
                >
                  <FileSpreadsheet className="h-4 w-4" />
                  Export Excel (.xlsx)
                </button>
                <button
                  onClick={handleSaveToDrive}
                  disabled={loading || driveState.status === "saving"}
                  className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700 disabled:opacity-50"
                >
                  <Cloud className="h-4 w-4" />
                  {driveState.status === "saving"
                    ? "Menyimpan..."
                    : "Simpan ke Google Drive"}
                </button>
                {driveState.status === "done" && driveState.link && (
                  <span className="inline-flex items-center gap-1.5 text-sm text-blue-700 bg-blue-50 border border-blue-200 rounded-md px-3 py-1.5">
                    Tersimpan di Drive:
                    <a
                      href={driveState.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium underline inline-flex items-center gap-1"
                    >
                      {driveState.fileName}{" "}
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  </span>
                )}
                {driveState.status === "error" && (
                  <span className="text-xs text-red-500">
                    {driveState.error}
                  </span>
                )}
                <span className="text-xs text-gray-400">
                  {result.functional.length +
                    result.negative.length +
                    result.boundary.length}{" "}
                  test cases siap di-download
                </span>
              </div>

              <SummaryCard summary={normalizeSummary(result.summary)} />

              {result.risk && <RiskCard risk={result.risk} />}

              <CoverageCard
                functional={result.functional.length}
                negative={result.negative.length}
                boundary={result.boundary.length}
              />

              {result.citations && (
                <CitationsCard citations={result.citations} />
              )}

              <TestCaseTabs
                functional={result.functional}
                negative={result.negative}
                boundary={result.boundary}
              />

              <div className="pt-2">
                <Button variant="outline" onClick={() => setStep(1)}>
                  Buat lagi dari awal
                </Button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
