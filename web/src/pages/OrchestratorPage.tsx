import OrchestratorForm from "@/components/orchestrator/OrchestratorForm";
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

import { Loader2, FileSpreadsheet, Cloud, ExternalLink } from "lucide-react";
import { useOrchestrator } from "@/store/orchestrator.store";
import { useAuth } from "@/store/auth.store";
import { normalizeSummary } from "@/lib/normalizers/normalizeSummary";

export default function OrchestratorPage() {
  const {
    result,
    loading,
    selectedDocumentIds,
    useRAG,
    useAdvancedRAG,
    useQueryExpansion,
    useReranking,
    setUseRAG,
    setUseAdvancedRAG,
    setUseQueryExpansion,
    setUseReranking,
    downloadExcel,
    saveToDrive,
    driveState,
  } = useOrchestrator();
  const accessToken = useAuth((s) => s.accessToken);

  const handleExportExcel = () => {
    if (accessToken) downloadExcel(accessToken);
  };

  const handleSaveToDrive = () => {
    if (accessToken) saveToDrive(accessToken);
  };

  return (
    <div className="space-y-10 p-6">
      {/* 🤖 PROVIDER (OpenRouter-only) */}
      <ProviderSelector />

      {/* OpenRouter model list */}
      <OllamaModelSelector />

      {/* 📄 DOCUMENT PICKER (V8 document-driven pipeline, multi-select) */}
      <DocumentPicker />

      {/* 📊 VOLUME SELECTOR (per-category TC targets) */}
      <VolumeSelector />

      {/* 🧠 ADVANCED RAG CONTROLS */}
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

      {/* ✅ FORM SELALU TAMPIL */}
      <OrchestratorForm />

      {/* ⏳ LOADING */}
      {loading && (
        <div className="p-6 bg-white shadow rounded-xl border border-gray-200 max-w-4xl">
          <div className="flex items-center gap-3 mb-3">
            <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
            <h3 className="text-lg font-semibold text-gray-700">
              Generating test cases...
            </h3>
          </div>
          <p className="text-sm text-gray-500 animate-pulse mb-4">
            {selectedDocumentIds.length > 0
              ? `✨ V8 pipeline: membaca ${selectedDocumentIds.length} dokumen → generate test cases. Est. 1-3 menit.`
              : "Est. 1-2 menit (cloud) / 3-5 menit (local)."}
          </p>
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4" />
            <div className="h-4 bg-gray-200 rounded animate-pulse w-1/2" />
            <div className="h-4 bg-gray-200 rounded animate-pulse w-2/3" />
          </div>
        </div>
      )}


      {/* ❌ BELUM ADA RESULT */}
      {!loading && !result && (
        <div className="text-gray-400 italic">
          Masukkan requirement dan klik Generate untuk melihat hasil.
        </div>
      )}

      {/* ✅ RESULT READY */}
      {result && (
        <>
          {/* 📤 Export actions */}
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
              {driveState.status === "saving" ? "Menyimpan..." : "Simpan ke Google Drive"}
            </button>
            {driveState.status === "done" && driveState.link && (
              <span className="inline-flex items-center gap-1.5 text-sm text-blue-700 bg-blue-50 border border-blue-200 rounded-md px-3 py-1.5">
                ✅ Tersimpan di Drive:
                <a
                  href={driveState.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium underline inline-flex items-center gap-1"
                >
                  {driveState.fileName} <ExternalLink className="h-3.5 w-3.5" />
                </a>
              </span>
            )}
            {driveState.status === "error" && (
              <span className="text-xs text-red-500">{driveState.error}</span>
            )}
            <span className="text-xs text-gray-400">
              {result.functional.length + result.negative.length + result.boundary.length} test cases siap di-download
            </span>
          </div>

          <SummaryCard
            summary={normalizeSummary(result.summary)}
          />

          {result.risk && <RiskCard risk={result.risk} />}

          <CoverageCard
            functional={result.functional.length}
            negative={result.negative.length}
            boundary={result.boundary.length}
          />

          {/* ✨ CITATIONS (if Advanced RAG was used) */}
          {result.citations && (
            <CitationsCard citations={result.citations} />
          )}

          <TestCaseTabs
            functional={result.functional}
            negative={result.negative}
            boundary={result.boundary}
          />
        </>
      )}
    </div>
  );
}
