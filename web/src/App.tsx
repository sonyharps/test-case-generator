// src/App.tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import MainLayout from "@/layouts/MainLayout.tsx";
import LandingPage from "@/pages/LandingPage";
import OrchestratorPage from "@/pages/OrchestratorPage.tsx";
import SessionHistoryPage from "@/pages/SessionHistoryPage.tsx";
import RequirementsLibraryPage from "@/pages/RequirementsLibraryPage.tsx";
import AnalyticsPage from "@/pages/AnalyticsPage.tsx";
import DokumenPage from "@/pages/DokumenPage.tsx";
import TimPage from "@/pages/admin/TimPage.tsx";
import UserManagementPage from "@/pages/admin/UserManagementPage.tsx";
import SquadManagementPage from "@/pages/admin/SquadManagementPage.tsx";
import ForbiddenPage from "@/pages/ForbiddenPage.tsx";
import LoginPage from "@/pages/LoginPage.tsx";
import RegisterPage from "@/pages/RegisterPage.tsx";
import ProtectedRoute from "@/components/auth/ProtectedRoute.tsx";

function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-right" richColors />
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected routes with layout */}
        <Route element={<MainLayout />}>
          <Route index element={<LandingPage />} />
          <Route
            path="/orchestrator"
            element={
              <ProtectedRoute>
                <OrchestratorPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <SessionHistoryPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/requirements"
            element={
              <ProtectedRoute>
                <RequirementsLibraryPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/analytics"
            element={
              <ProtectedRoute>
                <AnalyticsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/documents"
            element={
              <ProtectedRoute>
                <DokumenPage />
              </ProtectedRoute>
            }
          />

          {/* Admin-only routes (kabag+) — Tim = tab Anggota/Squad */}
          <Route
            path="/users"
            element={
              <ProtectedRoute allowedRoles={["kabag"]}>
                <TimPage />
              </ProtectedRoute>
            }
          />
          {/* Legacy deep-link (halaman berdiri sendiri) */}
          <Route
            path="/squads"
            element={
              <ProtectedRoute allowedRoles={["kabag"]}>
                <SquadManagementPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/users-legacy"
            element={
              <ProtectedRoute allowedRoles={["kabag"]}>
                <UserManagementPage />
              </ProtectedRoute>
            }
          />

          {/* Forbidden page */}
          <Route path="/forbidden" element={<ForbiddenPage />} />

          {/* fallback 404 */}
          <Route path="*" element={<div className="p-6">Page not found</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
