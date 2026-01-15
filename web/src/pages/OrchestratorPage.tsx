import OrchestratorForm from "@/components/orchestrator/OrchestratorForm";
import SummaryCard from "@/components/orchestrator/SummaryCard";
import TestCaseTabs from "@/components/orchestrator/TestCaseTabs";
import RiskCard from "@/components/orchestrator/RiskCard";
import CoverageCard from "@/components/orchestrator/CoverageCard";
import AdvancedRAGControls from "@/components/orchestrator/AdvancedRAGControls";
import CitationsCard from "@/components/orchestrator/CitationsCard";
import OllamaModelSelector from "@/components/orchestrator/OllamaModelSelector";
import ProviderSelector from "@/components/orchestrator/ProviderSelector";

import { useOrchestrator } from "@/store/orchestrator.store";
import { normalizeSummary } from "@/lib/normalizers/normalizeSummary";

export default function OrchestratorPage() {
  const {
    result,
    loading,
    provider,
    setProvider,
    useRAG,
    useAdvancedRAG,
    useQueryExpansion,
    useReranking,
    setUseRAG,
    setUseAdvancedRAG,
    setUseQueryExpansion,
    setUseReranking,
  } = useOrchestrator();

  return (
    <div className="space-y-10 p-6">
      {/* 🤖 PROVIDER SELECTOR */}
      <ProviderSelector
        provider={provider}
        onProviderChange={setProvider}
      />

      {/* Show model selector for all providers */}
      <OllamaModelSelector provider={provider} />

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
        <div className="text-gray-500">Generating test cases...</div>
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
