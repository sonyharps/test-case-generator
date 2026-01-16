import OrchestratorForm from "@/components/orchestrator/OrchestratorForm";
import SummaryCard from "@/components/orchestrator/SummaryCard";
import TestCaseTabs from "@/components/orchestrator/TestCaseTabs";
import RiskCard from "@/components/orchestrator/RiskCard";
import CoverageCard from "@/components/orchestrator/CoverageCard";
import AdvancedRAGControls from "@/components/orchestrator/AdvancedRAGControls";
import CitationsCard from "@/components/orchestrator/CitationsCard";
import OllamaModelSelector from "@/components/orchestrator/OllamaModelSelector";
import ProviderSelector from "@/components/orchestrator/ProviderSelector";
import SaveToRepositoryDialog from "@/components/orchestrator/SaveToRepositoryDialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { FolderPlus, FolderOpen, CheckCircle2, Loader2, Info, Users } from "lucide-react";

import { useOrchestrator } from "@/store/orchestrator.store";
import { useAuthStore } from "@/store/auth.store";
import { normalizeSummary } from "@/lib/normalizers/normalizeSummary";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import { getSessionRepositoryLink, type SessionRepositoryLink } from "@/api/history";
import { getCapacityStats, type CapacityStats } from "@/api/orchestrator";

export default function OrchestratorPage() {
  const token = useAuthStore((state) => state.token);
  const navigate = useNavigate();
  const [capacity, setCapacity] = useState<CapacityStats | null>(null);
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

  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [repoLink, setRepoLink] = useState<SessionRepositoryLink | null>(null);
  const [checkingRepo, setCheckingRepo] = useState(false);

  // Check if session is saved to repository
  useEffect(() => {
    if (result?.session_id && token) {
      checkRepositoryStatus(result.session_id);
    } else if (!result?.session_id) {
      setRepoLink(null);
    }
  }, [result?.session_id, token]);

  const checkRepositoryStatus = async (sessionId: string) => {
    setCheckingRepo(true);
    try {
      const link = await getSessionRepositoryLink(token, sessionId);
      setRepoLink(link);
    } catch {
      setRepoLink(null);
    } finally {
      setCheckingRepo(false);
    }
  };

  // Refresh repository status after saving
  const handleSavedToRepository = () => {
    if (result?.session_id) {
      checkRepositoryStatus(result.session_id);
    }
  };

  // Fetch capacity stats on mount and periodically
  useEffect(() => {
    if (!token) return;

    const fetchCapacity = async () => {
      try {
        const stats = await getCapacityStats(token);
        setCapacity(stats);
      } catch {
        // Silently fail if capacity endpoint is not available
        setCapacity(null);
      }
    };

    fetchCapacity();
    const interval = setInterval(fetchCapacity, 30000); // Update every 30s

    return () => clearInterval(interval);
  }, [token]);

  return (
    <div className="space-y-10 p-6">
      {/* 🤖 PROVIDER SELECTOR */}
      <ProviderSelector
        provider={provider}
        onProviderChange={setProvider}
      />

      {/* Capacity Indicator */}
      {capacity && (
        <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800/50 px-4 py-2 rounded-lg">
          <Users className="h-4 w-4" />
          <span>
            <span className="font-medium">{capacity.active_users}</span> / {capacity.max_concurrent_users} users active
          </span>
          <span className="text-gray-400">|</span>
          <span className={`font-medium ${
            capacity.status === "healthy" ? "text-green-600 dark:text-green-400" :
            capacity.status === "busy" ? "text-amber-600 dark:text-amber-400" :
            "text-red-600 dark:text-red-400"
          }`}>
            {capacity.capacity_percent}% capacity
          </span>
        </div>
      )}

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
        <div className="flex flex-col items-center justify-center py-16 space-y-4">
          <Loader2 className="h-12 w-12 text-blue-600 animate-spin" />
          <div className="text-center">
            <p className="text-lg font-medium text-gray-900">Generating test cases...</p>
            <p className="text-sm text-gray-500 mt-1">
              This may take a moment. Please wait.
            </p>
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
          {/* Actions Bar */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            {/* Repository Status */}
            <div className="flex items-center gap-2">
              {checkingRepo ? (
                <span className="text-sm text-gray-500">Checking repository...</span>
              ) : repoLink?.is_saved ? (
                <Badge variant="secondary" className="gap-1">
                  <CheckCircle2 className="h-3 w-3" />
                  Saved to: {repoLink.project_name} / {repoLink.suite_name}
                </Badge>
              ) : (
                <span className="text-sm text-gray-400">Not saved to repository</span>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              {repoLink?.is_saved && (
                <Button
                  variant="secondary"
                  className="gap-2"
                  onClick={() => navigate("/repository", {
                    state: { projectId: repoLink.project_id, suiteId: repoLink.suite_id }
                  })}
                >
                  <FolderOpen className="h-4 w-4" />
                  View in Repository
                </Button>
              )}
              <Button
                variant="outline"
                onClick={() => setSaveDialogOpen(true)}
                className="gap-2"
              >
                <FolderPlus className="h-4 w-4" />
                {repoLink?.is_saved ? "Update Repository" : "Save to Repository"}
              </Button>
            </div>
          </div>

          {/* Warnings (e.g., Free Tier Mode) */}
          {result.warnings && result.warnings.length > 0 && (
            <div className="space-y-3">
              {result.warnings.map((warning, idx) => (
                <Alert key={idx} variant="default" className="border-amber-200 bg-amber-50 dark:bg-amber-950/20">
                  <Info className="h-4 w-4 text-amber-600" />
                  <AlertTitle className="text-amber-800 dark:text-amber-400">
                    {warning.title}
                  </AlertTitle>
                  <AlertDescription className="text-amber-700 dark:text-amber-300">
                    {warning.message}
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          )}

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

      {/* Save to Repository Dialog */}
      <SaveToRepositoryDialog
        open={saveDialogOpen}
        onClose={() => {
          setSaveDialogOpen(false);
          handleSavedToRepository();
        }}
        orchestratorResult={result}
      />
    </div>
  );
}
