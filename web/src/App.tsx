// src/App.tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import MainLayout from "@/layouts/MainLayout.tsx";
import LandingPage from "@/pages/LandingPage";
import OrchestratorPage from "@/pages/OrchestratorPage.tsx";
import SessionHistoryPage from "@/pages/SessionHistoryPage.tsx";
import RequirementsLibraryPage from "@/pages/RequirementsLibraryPage.tsx";
import AnalyticsPage from "@/pages/AnalyticsPage.tsx";
import DocumentsPage from "@/pages/DocumentsPage.tsx";
import TestRepositoryPage from "@/pages/TestRepositoryPage.tsx";
import TestRunsPage from "@/pages/TestRunsPage.tsx";
import TestReportsPage from "@/pages/TestReportsPage.tsx";
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
                <DocumentsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/test-repository"
            element={
              <ProtectedRoute>
                <TestRepositoryPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/test-runs"
            element={
              <ProtectedRoute>
                <TestRunsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/test-reports"
            element={
              <ProtectedRoute>
                <TestReportsPage />
              </ProtectedRoute>
            }
          />
          {/* fallback 404 */}
          <Route path="*" element={<div className="p-6">Page not found</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
