// src/layouts/MainLayout.tsx
import { Outlet, NavLink } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/", label: "Home" },
  { to: "/orchestrator", label: "Orchestrator" },
  { to: "/pdf-history", label: "PDF History" },
];

export default function MainLayout() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col">
      {/* Top Navbar */}
      <header className="h-14 border-b border-slate-200 bg-white/80 backdrop-blur flex items-center px-4 justify-between">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-blue-500 via-purple-500 to-orange-400" />
          <div className="flex flex-col leading-tight">
            <span className="font-semibold text-sm">AI QA Orchestrator</span>
            <span className="text-[11px] text-slate-500">
              Enterprise Test Case Engine
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-500 hidden sm:inline">
            Model: <span className="font-medium text-slate-700">llama3.1:8b</span>
          </span>
          <Button
            size="sm"
            className="bg-blue-600 hover:bg-blue-700 text-xs rounded-full px-4"
          >
            Generate Test Case
          </Button>
        </div>
      </header>

      {/* Body: Sidebar + Content */}
      <div className="flex flex-1">
        {/* Sidebar */}
        <aside className="hidden md:flex w-56 border-r border-slate-200 bg-white/90 backdrop-blur flex-col py-4">
          <nav className="flex-1 px-2 space-y-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  cn(
                    "flex items-center px-3 py-2 rounded-md text-sm transition-colors",
                    "text-slate-600 hover:text-slate-900 hover:bg-slate-100",
                    isActive &&
                      "bg-blue-50 text-blue-700 border border-blue-100 font-medium"
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="px-3 py-3 border-t border-slate-100 text-[11px] text-slate-500">
            v0.1 • Internal QA
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
