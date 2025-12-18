// src/pages/OrchestratorPage.tsx

import { useState } from "react";
import { useOrchestrator } from "@/store/orchestrator.store";

import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";

import RiskMeter from "@/components/orchestrator/RiskMeter";
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
    setRequirement(localReq.trim());
    await run();
  }

  async function handlePdf() {
    await downloadPdf(localReq);
  }

  return (
    <div className="px-10 py-10 space-y-12 max-w-5xl mx-auto animate-fadeIn">

      {/* ===========================
          INPUT SECTION (PREMIUM)
      ============================ */}
      <Card className="bg-white/95 backdrop-blur-md shadow-lg rounded-xl border border-gray-100">
        <CardHeader>
          <CardTitle className="text-2xl font-bold tracking-tight text-gray-900">
            Orchestrator Engine
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">
          
          <textarea
            value={localReq}
            onChange={(e) => setLocalReq(e.target.value)}
            placeholder="Masukkan requirement, contoh: User dapat login dengan email dan password valid"
            className="w-full p-4 border rounded-lg text-sm bg-white shadow-inner 
                       focus:ring-2 focus:ring-blue-400 focus:outline-none transition-all"
            rows={4}
          />

          {/* ======= CONFIGURATION ======= */}
          <div className="grid grid-cols-3 gap-6 text-sm">

            {/* MODEL */}
            <div className="space-y-1">
              <label className="font-medium text-gray-700">Model LLM</label>
              <input
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full mt-1 p-2 border rounded bg-white shadow-sm
                           focus:ring-2 focus:ring-blue-300 transition-all"
              />
            </div>

            {/* CHECKBOXES */}
            <label className="flex items-center gap-2 mt-7 text-gray-700">
              <input
                type="checkbox"
                checked={generateBoundary}
                onChange={(e) => setGenerateBoundary(e.target.checked)}
              />
              Generate Boundary Test
            </label>

            <label className="flex items-center gap-2 mt-7 text-gray-700">
              <input
                type="checkbox"
                checked={includeRisk}
                onChange={(e) => setIncludeRisk(e.target.checked)}
              />
              Include Risk Assessment
            </label>

          </div>

          {/* ACTION BUTTONS */}
          <div className="flex gap-4">
            <Button
              disabled={loading || !localReq.trim()}
              onClick={handleRun}
              className="px-6 h-10 text-sm font-medium shadow-md"
            >
              {loading ? "Processing..." : "Run Orchestrator"}
            </Button>

            <Button
              variant="outline"
              disabled={loading || !localReq.trim()}
              onClick={handlePdf}
              className="px-6 h-10 text-sm font-medium"
            >
              Export PDF
            </Button>
          </div>

          {error && <p className="text-red-600 text-sm">{error}</p>}
        </CardContent>
      </Card>




      {/* ======================================
           RESULT SECTION (PREMIUM RENDER)
      ======================================= */}
      {result && (
        <section className="space-y-10 animate-fadeIn">

          {/* SUMMARY */}
          <Card className="bg-white shadow-lg rounded-xl border border-gray-100">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-gray-900 tracking-tight">
                Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <SummaryCard summary={result.summary} />
            </CardContent>
          </Card>



          {/* COVERAGE — RISK — METADATA */}
          <div className="grid grid-cols-3 gap-6">

            {/* COVERAGE */}
            <Card className="bg-white shadow-md rounded-xl border border-gray-100">
              <CardHeader>
                <CardTitle className="text-md font-semibold tracking-tight">
                  Coverage
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm space-y-1 text-gray-800">
                <div>Functional: {JSON.stringify(result.coverage_matrix.functional_count, null, 2)}</div>
                <div>Negative: {JSON.stringify(result.coverage_matrix.negative_count, null, 2)}</div>
                <div>Boundary: {JSON.stringify(result.coverage_matrix.boundary_count, null, 2)}</div>
              </CardContent>
            </Card>

            {/* RISK */}
            <Card className="bg-white shadow-md rounded-xl border border-gray-100">
              <CardHeader>
                <CardTitle className="text-md font-semibold tracking-tight">
                  Risk Assessment
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-gray-800 flex flex-col items-center">
                <RiskMeter level={JSON.stringify(result.risk.level, null, 2)} />
                <ul className="mt-4 list-disc pl-5 space-y-1 text-left w-full">
                  {result.risk.notes.map((n, i) => (
                    <li key={i}>{n}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            {/* METADATA */}
            <Card className="bg-white shadow-md rounded-xl border border-gray-100">
              <CardHeader>
                <CardTitle className="text-md font-semibold tracking-tight">
                  Metadata
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm space-y-1 text-gray-800">
                <div>Model: {JSON.stringify(result.metadata?.model, null, 2)}</div>
                <div>Generated: {JSON.stringify(result.metadata?.time, null, 2)}</div>
              </CardContent>
            </Card>

          </div>




          {/* ===========================
               TABS + ACCORDION TCs
          ============================ */}
          <Card className="bg-white shadow-lg rounded-xl border border-gray-100">
            <CardHeader>
              <CardTitle className="text-lg font-semibold tracking-tight">
                Test Cases
              </CardTitle>
            </CardHeader>

            <CardContent>
              <Tabs defaultValue="functional" className="w-full">

                {/* TAB LIST */}
                <TabsList className="mb-6 bg-gray-100 p-1 rounded-lg shadow-inner">
                  <TabsTrigger
                    value="functional"
                    className="data-[state=active]:bg-white data-[state=active]:shadow-sm 
                               rounded-md px-4 py-2 text-sm font-medium transition-all"
                  >
                    Functional
                  </TabsTrigger>

                  <TabsTrigger
                    value="negative"
                    className="data-[state=active]:bg-white data-[state=active]:shadow-sm 
                               rounded-md px-4 py-2 text-sm font-medium transition-all"
                  >
                    Negative
                  </TabsTrigger>

                  <TabsTrigger
                    value="boundary"
                    className="data-[state=active]:bg-white data-[state=active]:shadow-sm 
                               rounded-md px-4 py-2 text-sm font-medium transition-all"
                  >
                    Boundary
                  </TabsTrigger>
                </TabsList>


                {/* FUNCTIONAL */}
                <TabsContent value="functional">
                  <TCAccordion data={result.functional} />
                </TabsContent>

                {/* NEGATIVE */}
                <TabsContent value="negative">
                  <TCAccordion data={result.negative} />
                </TabsContent>

                {/* BOUNDARY */}
                <TabsContent value="boundary">
                  <TCAccordion data={result.boundary} />
                </TabsContent>

              </Tabs>
            </CardContent>
          </Card>

        </section>
      )}
    </div>
  );
}




/* ============================================
   PREMIUM TEST CASE CARD — JIRA/TESTRAIL STYLE
=============================================== */

function TCAccordion({ data }: { data: any[] }) {
  if (!Array.isArray(data) || data.length === 0) {
    return <p className="text-sm text-gray-500">Tidak ada test case.</p>;
  }

  return (
    <div className="space-y-4">
      {data.map((tc) => (
        <div
          key={tc.tc_id}
          className="border border-gray-200 bg-white rounded-xl shadow-sm hover:shadow-md transition-all p-5"
        >
          {/* HEADER */}
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <span className="text-blue-700">{tc.tc_id}</span>
                — {tc.title}
              </h3>

              {/* BADGES */}
              <div className="flex gap-2 mt-2">
                {tc.tc_id.startsWith("TC-F") && (
                  <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded-md">
                    Functional
                  </span>
                )}

                {tc.tc_id.startsWith("TC-N") && (
                  <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-700 rounded-md">
                    Negative
                  </span>
                )}

                {tc.tc_id.startsWith("TC-B") && (
                  <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-md">
                    Boundary
                  </span>
                )}

                {tc.boundary_type && (
                  <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded-md">
                    {tc.boundary_type}
                  </span>
                )}
              </div>
            </div>
          </div>

          <hr className="mb-4" />

          {/* BODY — TABLE STYLE SECTIONS */}
          <div className="space-y-6">

            {/* Preconditions */}
            {tc.preconditions?.length > 0 && (
              <div>
                <div className="text-sm font-semibold mb-1 text-gray-900">Preconditions</div>
                <ul className="list-disc ml-6 text-sm text-gray-700 space-y-1">
                  {tc.preconditions.map((p: any, i: number) => (
                    <li key={i}>{typeof p === "string" ? p : JSON.stringify(p)}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Steps (Numbered) */}
            {tc.steps?.length > 0 && (
              <div>
                <div className="text-sm font-semibold mb-1 text-gray-900">Steps</div>
                <ol className="list-decimal ml-6 text-sm text-gray-700 space-y-1">
                  {tc.steps.map((s: any, i: number) => (
                    <li key={i}>
                      {typeof s === "string" ? s : JSON.stringify(s)}
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {/* Expected Result (Checklist style) */}
            {tc.expected_result?.length > 0 && (
              <div>
                <div className="text-sm font-semibold mb-1 text-gray-900">Expected Result</div>
                <ul className="space-y-1 ml-1">
                  {tc.expected_result.map((e: any, i: number) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 text-sm text-gray-700"
                    >
                      <span className="text-green-600 mt-1">✔</span>
                      <span>{typeof e === "string" ? e : JSON.stringify(e)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

          </div>
        </div>
      ))}
    </div>
  );
}
