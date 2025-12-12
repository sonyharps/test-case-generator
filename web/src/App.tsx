// src/App.tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import MainLayout from "@/layouts/MainLayout.tsx";
import LandingPage from "@/pages/LandingPage";
import OrchestratorPage from "@/pages/OrchestratorPage.tsx";
import PdfHistoryPage from "@/pages/PdfHistoryPage.tsx";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route index element={<LandingPage />} />
          <Route path="/orchestrator" element={<OrchestratorPage />} />
          <Route path="/pdf-history" element={<PdfHistoryPage />} />
          {/* fallback 404 simple */}
          <Route path="*" element={<div className="p-6">Page not found</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
