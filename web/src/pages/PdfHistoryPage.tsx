// src/pages/PdfHistoryPage.tsx
import { Card, CardContent } from "@/components/ui/card";

const MOCK_HISTORY = [
  {
    id: "PDF-2025-0001",
    requirement: "User dapat login dengan email dan password yang valid",
    createdAt: "2025-12-09 14:05",
    risk: "Low",
  },
  {
    id: "PDF-2025-0002",
    requirement: "User dapat reset password via email OTP",
    createdAt: "2025-12-10 09:30",
    risk: "Medium",
  },
];

export default function PdfHistoryPage() {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">
          PDF Orchestration History
        </h2>
        <p className="text-sm text-slate-500">
          Daftar report PDF yang pernah di-generate. Nanti bisa disambungkan
          dengan backend storage.
        </p>
      </div>

      <Card className="border-slate-200">
        <CardContent className="p-0">
          <div className="grid grid-cols-[1.3fr,1.8fr,1fr,0.8fr] text-xs font-medium text-slate-500 border-b border-slate-100 px-4 py-2">
            <div>ID</div>
            <div>Requirement</div>
            <div>Generated At</div>
            <div>Risk</div>
          </div>

          <div className="divide-y divide-slate-100 text-xs">
            {MOCK_HISTORY.map((item) => (
              <div
                key={item.id}
                className="grid grid-cols-[1.3fr,1.8fr,1fr,0.8fr] px-4 py-2 items-center"
              >
                <div className="font-mono text-[11px] text-slate-700">
                  {item.id}
                </div>
                <div className="text-slate-700 truncate">
                  {item.requirement}
                </div>
                <div className="text-slate-500">{item.createdAt}</div>
                <div className="text-slate-700">{item.risk}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
