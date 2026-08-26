import { Button } from "@/components/ui/button";
import { Loader2, Sparkles, RefreshCw } from "lucide-react";
import { useOrchestrator } from "@/store/orchestrator.store";
import { useAuth } from "@/store/auth.store";

export default function OrchestratorForm() {
  const {
    requirement,
    setRequirement,
    run,
    loading,
    result,
    selectedDocumentIds,
  } = useOrchestrator();

  const accessToken = useAuth((state) => state.accessToken);

  const handleGenerate = () => {
    if (accessToken) {
      run(accessToken);
    }
  };

  // Estimate based on current provider config. Cloud (GLM/Gemini/Groq) is
  // fast (~2 min); local is slow (2-5 min). Shown only while loading.
  const estimateLabel = selectedDocumentIds.length > 0
    ? `Est. ~1-3 menit (cloud, ${selectedDocumentIds.length} dokumen)`
    : "Est. ~1-2 menit (cloud) / 3-5 menit (local)";

  const hasResult = !!result;

  return (
    <div className="p-6 bg-white shadow rounded-xl border border-gray-200 max-w-4xl">
      <h2 className="text-lg font-semibold mb-2">Requirement under test</h2>

      <textarea
        value={requirement}
        onChange={(e) => setRequirement(e.target.value)}
        className="w-full border h-32 p-3 rounded-lg"
        placeholder="Enter your requirement here..."
      />

      <div className="mt-4 flex items-center gap-3">
        <Button onClick={handleGenerate} disabled={loading}>
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Generating test cases...
            </>
          ) : hasResult ? (
            <>
              <RefreshCw className="h-4 w-4 mr-2" />
              Generate Ulang
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4 mr-2" />
              Generate Test Cases
            </>
          )}
        </Button>

        {loading && (
          <span className="text-sm text-gray-500 animate-pulse">
            {estimateLabel}
          </span>
        )}

        {hasResult && !loading && (
          <span className="text-sm text-gray-500">
            {selectedDocumentIds.length > 0
              ? `✨ Generated from ${selectedDocumentIds.length} document(s) (V8 pipeline)`
              : `✨ Ready`}
          </span>
        )}
      </div>
    </div>
  );
}
