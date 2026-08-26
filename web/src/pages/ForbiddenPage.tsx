// src/pages/ForbiddenPage.tsx
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ShieldAlert } from "lucide-react";

export default function ForbiddenPage() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <ShieldAlert className="w-16 h-16 text-red-500 mb-4" />
      <h1 className="text-2xl font-bold text-slate-900 mb-2">403 — Access Denied</h1>
      <p className="text-slate-600 mb-6 max-w-md">
        You don't have permission to view this page. If you believe this is a
        mistake, contact an administrator.
      </p>
      <Button onClick={() => navigate("/")}>Back to Home</Button>
    </div>
  );
}
