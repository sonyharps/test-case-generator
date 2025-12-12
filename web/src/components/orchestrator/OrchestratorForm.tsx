import { Button } from "@/components/ui/button";
import { useOrchestrator } from "@/store/orchestrator.store";

export default function OrchestratorForm() {
  const { requirement, setRequirement, orchestrate, loading } = useOrchestrator();

  return (
    <div className="p-6 bg-white shadow rounded-xl border border-gray-200 max-w-4xl">
      <h2 className="text-lg font-semibold mb-2">Requirement under test</h2>

      <textarea
        value={requirement}
        onChange={(e) => setRequirement(e.target.value)}
        className="w-full border h-32 p-3 rounded-lg"
        placeholder="Masukkan requirement lu di sini..."
      />

      <Button onClick={orchestrate} className="mt-4" disabled={loading}>
        {loading ? "Generating..." : "Generate Test Cases"}
      </Button>
    </div>
  );
}
