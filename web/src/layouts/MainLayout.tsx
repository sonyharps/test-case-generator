// src/layouts/MainLayout.tsx
import { Outlet, NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";
import UserProfile from "@/components/auth/UserProfile";
import { useAuth } from "@/store/auth.store";
import { hasMinRole } from "@/lib/roles";

interface NavItem {
  to: string;
  label: string;
  /** Minimum role required to SEE this item. Omit = everyone. */
  minRole?: string;
}

// 2026-09: disederhanakan dari 8 menu teknis → 5 menu bahasa tugas (+ Tim utk admin).
// Requirements Library & Squads jadi tab di dalam Dokumen / Tim.
const navItems: NavItem[] = [
  { to: "/", label: "Beranda" },
  { to: "/orchestrator", label: "Buat Test Case" },
  { to: "/documents", label: "Dokumen" },
  { to: "/history", label: "Riwayat & Export" },
  { to: "/analytics", label: "Laporan" },
  // Admin-only
  { to: "/users", label: "Tim", minRole: "kabag" },
];

export default function MainLayout() {
  const user = useAuth((s) => s.user);
  const visibleItems = navItems.filter(
    (item) => !item.minRole || hasMinRole(user?.role, item.minRole)
  );

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col">
      {/* Top Navbar */}
      <header className="h-14 border-b border-slate-200 bg-white flex items-center px-4 justify-between">
        <div className="flex items-center gap-2.5">
          <div className="h-7 w-7 rounded bg-slate-900 text-white flex items-center justify-center text-[11px] font-bold tracking-tight">
            QA
          </div>
          <div className="flex flex-col leading-tight">
            <span className="font-semibold text-sm">QA Test Case Generator</span>
            <span className="text-[11px] text-slate-500">
              Internal QA Platform
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <UserProfile />
        </div>
      </header>

      {/* Body: Sidebar + Content */}
      <div className="flex flex-1">
        {/* Sidebar */}
        <aside className="hidden md:flex w-60 border-r border-slate-200 bg-white flex-col py-4">
          <nav className="flex-1 px-2 space-y-0.5">
            {visibleItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  cn(
                    "flex items-center px-3 py-2 rounded-md text-sm transition-colors border border-transparent",
                    "text-slate-600 hover:text-slate-900 hover:bg-slate-100",
                    isActive &&
                      "bg-slate-900 text-white border-slate-900 font-medium hover:bg-slate-900 hover:text-white"
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="px-3 py-3 border-t border-slate-100 text-[11px] text-slate-500">
            Internal QA · v1.0
          </div>
        </aside>

        {/* Content */}
        <main className="flex-1 px-3 sm:px-6 py-4">
          <div className="max-w-6xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
