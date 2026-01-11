import { BadgeCheck, ListChecks } from "lucide-react";
import type { SummaryVM } from "@/lib/normalizers/normalizeSummary";

export default function SummaryCard({ summary }: { summary: SummaryVM }) {
  if (!summary) return null;

  return (
    <div className="space-y-6 text-gray-800">

      {/* HEADER */}
      <div className="flex items-center gap-3">
        <BadgeCheck className="w-6 h-6 text-blue-600" />
        <h2 className="text-xl font-bold tracking-tight text-gray-900">
          Requirement Summary
        </h2>
      </div>

      {/* TOP ROW */}
      <div className="grid grid-cols-3 gap-6">
        <div>
          <p className="text-xs text-gray-500 font-semibold">ID</p>
          <p className="text-base font-medium mt-1">{summary.id || "—"}</p>
        </div>

        <div>
          <p className="text-xs text-gray-500 font-semibold">Prioritas</p>
          <span className="mt-1 inline-flex px-3 py-1 text-sm font-medium rounded-full 
                           bg-blue-50 text-blue-700 border border-blue-200">
            {summary.prioritas || "—"}
          </span>
        </div>

        <div>
          <p className="text-xs text-gray-500 font-semibold">Kategori</p>
          <span className="mt-1 inline-flex px-3 py-1 text-sm font-medium rounded-full 
                           bg-gray-100 border text-gray-700">
            {summary.kategori || "—"}
          </span>
        </div>
      </div>

      {/* NAMA */}
      <div>
        <p className="text-xs text-gray-500 font-semibold">Nama Requirement</p>
        <p className="text-lg font-semibold mt-1">
          {summary.nama || "—"}
        </p>
      </div>

      {/* DESKRIPSI */}
      <div>
        <p className="text-xs text-gray-500 font-semibold">Deskripsi</p>
        <div className="mt-2 bg-gray-50 rounded-lg border p-4 leading-relaxed text-[15px]">
          {summary.deskripsi || "—"}
        </div>
      </div>

      {/* FITUR KUNCI */}
      {summary.fiturKunci?.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <ListChecks className="w-4 h-4 text-gray-600" />
            <span className="text-sm font-semibold text-gray-700">
              Fitur Kunci
            </span>
          </div>

          <ul className="ml-6 list-disc space-y-1">
            {summary.fiturKunci.map((item, i) => (
              <li key={i} className="text-gray-700 text-sm">
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
