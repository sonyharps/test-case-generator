// src/pages/LandingPage.tsx
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function LandingPage() {
  return (
    <div className="space-y-8">
      {/* Hero */}
      <section className="grid gap-6 md:grid-cols-[1.4fr,1fr] items-center">
        <div className="space-y-4">
          <span className="inline-flex items-center gap-2 rounded-full bg-blue-50 text-blue-700 border border-blue-100 px-3 py-1 text-xs font-medium">
            🚀 Enterprise AI QA Orchestrator
          </span>
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-semibold text-slate-900 tracking-tight">
            Auto-generate{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-purple-500 to-orange-500">
              test cases
            </span>{" "}
            from your requirements.
          </h1>
          <p className="text-sm sm:text-base text-slate-600 max-w-xl">
            Paste your requirement, let the engine orchestrate functional,
            negative, and boundary test cases, plus a PDF report ready for
            audit and UAT.
          </p>

          <div className="flex flex-wrap items-center gap-3">
            <Button className="bg-blue-600 hover:bg-blue-700">
              Start Orchestrating
            </Button>
            <Button
              variant="outline"
              className="border-purple-200 text-purple-700 hover:bg-purple-50"
            >
              View Sample Report
            </Button>
          </div>

          <div className="flex flex-wrap gap-6 pt-2 text-xs text-slate-500">
            <div>
              <div className="font-semibold text-slate-900 text-sm">
                +300% coverage
              </div>
              vs manual test design
            </div>
            <div>
              <div className="font-semibold text-slate-900 text-sm">
                &lt; 30s
              </div>
              to generate full suite
            </div>
            <div>
              <div className="font-semibold text-slate-900 text-sm">
                AI risk scoring
              </div>
              built into every run
            </div>
          </div>
        </div>

        {/* Right summary card */}
        <Card className="border-blue-100 shadow-sm">
          <CardContent className="p-4 space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="font-medium text-slate-800">
                Last Orchestration
              </span>
              <span className="rounded-full bg-emerald-50 text-emerald-700 px-2 py-0.5 text-[10px] border border-emerald-100">
                OK
              </span>
            </div>
            <div className="text-xs text-slate-500">
              Requirement: <span className="text-slate-700">Login valid user</span>
            </div>

            <div className="grid grid-cols-3 gap-3 text-center pt-2">
              <div className="rounded-md bg-blue-50 py-2">
                <div className="text-sm font-semibold text-blue-700">12</div>
                <div className="text-[11px] text-blue-600">Functional</div>
              </div>
              <div className="rounded-md bg-orange-50 py-2">
                <div className="text-sm font-semibold text-orange-700">8</div>
                <div className="text-[11px] text-orange-600">Negative</div>
              </div>
              <div className="rounded-md bg-purple-50 py-2">
                <div className="text-sm font-semibold text-purple-700">5</div>
                <div className="text-[11px] text-purple-600">Boundary</div>
              </div>
            </div>

            <div className="pt-2 space-y-1">
              <div className="flex justify-between text-xs text-slate-500">
                <span>Risk level</span>
                <span className="font-medium text-amber-600">Medium</span>
              </div>
              <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
                <div className="h-full w-2/3 bg-gradient-to-r from-emerald-400 via-amber-400 to-red-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Simple features row */}
      <section className="grid gap-4 sm:grid-cols-3">
        <Card className="border-slate-200">
          <CardContent className="p-4 space-y-1">
            <div className="text-sm font-semibold text-slate-900">
              Functional / Negative / Boundary
            </div>
            <p className="text-xs text-slate-500">
              Engine split test cases by intent so QA can review fast.
            </p>
          </CardContent>
        </Card>
        <Card className="border-slate-200">
          <CardContent className="p-4 space-y-1">
            <div className="text-sm font-semibold text-slate-900">
              PDF Orchestrator
            </div>
            <p className="text-xs text-slate-500">
              One-click export to PDF with risk matrix and coverage summary.
            </p>
          </CardContent>
        </Card>
        <Card className="border-slate-200">
          <CardContent className="p-4 space-y-1">
            <div className="text-sm font-semibold text-slate-900">
              LangChain ready
            </div>
            <p className="text-xs text-slate-500">
              Designed to plug into LangChain agent workflows in the next phase.
            </p>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
