import OrchestratorForm from "@/components/orchestrator/OrchestratorForm";
import OrchestratorSummary from "@/components/orchestrator/OrchestratorSummary";
import TestCaseTabs from "@/components/orchestrator/TestCaseTabs";
import CoverageStats from "@/components/orchestrator/CoverageStats";
import RiskMeter from "@/components/orchestrator/RiskMeter";
import { useOrchestrator } from "@/store/orchestrator.store";

export default function OrchestratorPage() {
  const { result } = useOrchestrator();

  return (
    <div className="p-10 space-y-10">
      <OrchestratorForm />

      {result && (
        <>
          <OrchestratorSummary summary={result.summary || ""} />

          <div className="grid grid-cols-3 gap-6">
            <CoverageStats data={result.coverage_matrix!} />
            <RiskMeter
              level={result.risk?.level || "Low"}
              notes={result.risk?.notes || []}
            />
          </div>

          <TestCaseTabs
            functional={result.functional || []}
            negative={result.negative || []}
            boundary={result.boundary || []}
          />
        </>
      )}
    </div>
  );
}
