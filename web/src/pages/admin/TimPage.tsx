// src/pages/admin/TimPage.tsx
// Wrapper: menu "Tim" — Anggota / Squad / Proyek (kabag/admin).
import { useState } from "react";
import UserManagementPage from "@/pages/admin/UserManagementPage";
import SquadManagementPage from "@/pages/admin/SquadManagementPage";
import ProjectsTab from "@/pages/admin/ProjectsTab";
import { cn } from "@/lib/utils";

const TABS = [
  { key: "anggota", label: "Anggota" },
  { key: "squad", label: "Squad" },
  { key: "proyek", label: "Proyek" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

export default function TimPage() {
  const [tab, setTab] = useState<TabKey>("anggota");

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Tim</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          Kelola anggota, squad &amp; proyek (khusus kabag/admin).
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

      {tab === "anggota" && <UserManagementPage />}
      {tab === "squad" && <SquadManagementPage />}
      {tab === "proyek" && <ProjectsTab />}
    </div>
  );
}
