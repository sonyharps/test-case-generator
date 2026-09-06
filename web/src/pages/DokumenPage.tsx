// src/pages/DokumenPage.tsx
// Wrapper: menu "Dokumen" — gabung Documents + Requirements Library jadi tab.
import { useState } from "react";
import DocumentsPage from "@/pages/DocumentsPage";
import RequirementsLibraryPage from "@/pages/RequirementsLibraryPage";
import { cn } from "@/lib/utils";

const TABS = [
  { key: "dokumen", label: "Dokumen" },
  { key: "requirements", label: "Requirements Library" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

export default function DokumenPage() {
  const [tab, setTab] = useState<TabKey>("dokumen");

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Dokumen</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          Semua bahan untuk generate — PRD, user story, requirement.
        </p>
      </div>

      <div className="flex gap-1 rounded-lg bg-slate-100 p-1 w-fit">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              "px-4 py-1.5 rounded-md text-sm font-medium transition-colors",
              tab === t.key
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "dokumen" ? <DocumentsPage /> : <RequirementsLibraryPage />}
    </div>
  );
}
