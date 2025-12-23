import { useState } from "react";
import { useOrchestrator } from "@/store/orchestrator.store";

import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

import RiskMeter from "@/components/orchestrator/RiskMeter";
import TCAccordion from "@/components/orchestrator/TCAccordion";
import SummaryCard from "@/components/orchestrator/SummaryCard";

export default function OrchestratorPage() {
  const orch = useOrchestrator();

  const {
    requirement,
    model,
    generateBoundary,
    includeRisk,
    result,
    error,
    loading,
    setRequirement,
    setModel,
    setGenerateBoundary,
    setIncludeRisk,
    run,
    downloadPdf,
  } = orch;

  const [localReq, setLocalReq] = useState(requirement);

  async function handleRun() {
    if (!localReq.trim()) return;
    setRequirement(localReq.trim());
    await run();
  }

  async function handlePdf() {
    if (!localReq.trim()) return;
    await downloadPdf(localReq);
  }

  // =============================
  // SAFE EXTRACTORS (ANTI BLANK)
  // =============================
  const summary = result?.summary ?? null;

  const functional = Array.isArray(result?.functional)
    ? result.functional
    : [];

  const negative = Array.isArray(result?.negative)
    ? result.negative
    : [];

  const boundary = Array.isArray(result?.boundary)
    ? result.boundary
    : [];

  const coverage = result?.coverage_matrix ?? {
    functional_count: 0,
    negative_count: 0,
    boundary_count: 0,
  };

  const risk = result?.risk ?? { level: "N/A", notes: [] };

  const metadata = {
    model: result?.metadata?.model ?? "-",

    domain:
      result?.metadata && "domain" in result.metadata
        ? (result.metadata as { domain: string }).domain
        : "-",

    time: result?.metadata?.time ?? "-",
  };

  return (
    <div className="px-10 py-10 space-y-12 max-w-5xl mx-auto animate-fadeIn">
      {/* INPUT */}
      <Card className="bg-white shadow-lg rounded-xl border border-gray-100">
        <CardHeader>
          <CardTitle className="text-2xl font-bold tracking-tight">
            Orchestrator Engine
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">
          <textarea
            value={localReq}
            onChange={(e) => setLocalReq(e.target.value)}
            placeholder="Masukkan requirement..."
            className="w-full p-4 border rounded-lg text-sm bg-white shadow-inner"
            rows={4}
          />

          <div className="grid grid-cols-3 gap-6 text-sm">
            <div>
              <label className="font-medium">Model LLM</label>
              <input
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full mt-1 p-2 border rounded"
              />
            </div>

            <label className="flex items-center gap-2 mt-7">
              <input
                type="checkbox"
                checked={generateBoundary}
                onChange={(e) => setGenerateBoundary(e.target.checked)}
              />
              Generate Boundary
            </label>

            <label className="flex items-center gap-2 mt-7">
              <input
                type="checkbox"
                checked={includeRisk}
                onChange={(e) => setIncludeRisk(e.target.checked)}
              />
              Include Risk
            </label>
          </div>

          <div className="flex gap-4">
            <Button disabled={loading} onClick={handleRun}>
              {loading ? "Processing..." : "Run Orchestrator"}
            </Button>

            <Button
              variant="outline"
              disabled={loading}
              onClick={handlePdf}
            >
              Export PDF
            </Button>
          </div>

          {error && (
            <p className="text-red-600 text-sm whitespace-pre-wrap">{error}</p>
          )}
        </CardContent>
      </Card>

      {/* RESULT */}
      {result && (
        <section className="space-y-10">
          {/* SUMMARY */}
          <Card>
            <CardHeader>
              <CardTitle>Summary</CardTitle>
            </CardHeader>
            <CardContent>
              {summary ? (
                <SummaryCard summary={summary} />
              ) : (
                <p className="text-sm italic text-gray-500">
                  Summary tidak tersedia
                </p>
              )}
            </CardContent>
          </Card>

          {/* COVERAGE / RISK / META */}
          <div className="grid grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Coverage</CardTitle>
              </CardHeader>
              <CardContent className="text-sm">
                <div>Functional: {coverage.functional_count}</div>
                <div>Negative: {coverage.negative_count}</div>
                <div>Boundary: {coverage.boundary_count}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Risk</CardTitle>
              </CardHeader>
              <CardContent>
                <RiskMeter level={risk.level} />
                <ul className="mt-2 list-disc pl-5 text-sm">
                  {(risk.notes ?? []).map((n: string, i: number) => (
                    <li key={i}>{n}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Metadata</CardTitle>
              </CardHeader>
              <CardContent className="text-sm">
                <div>Model: {metadata.model}</div>
                <div>Domain: {metadata.domain}</div>
                <div>Generated: {metadata.time}</div>
              </CardContent>
            </Card>
          </div>

          {/* TEST CASES */}
          <Card>
            <CardHeader>
              <CardTitle>Test Cases</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="functional">
                <TabsList>
                  <TabsTrigger value="functional">Functional</TabsTrigger>
                  <TabsTrigger value="negative">Negative</TabsTrigger>
                  <TabsTrigger value="boundary">Boundary</TabsTrigger>
                </TabsList>

                <TabsContent value="functional">
                  <TCAccordion data={functional} />
                </TabsContent>

                <TabsContent value="negative">
                  <TCAccordion data={negative} />
                </TabsContent>

                <TabsContent value="boundary">
                  <TCAccordion data={boundary} />
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </section>
      )}
    </div>
  );
}
