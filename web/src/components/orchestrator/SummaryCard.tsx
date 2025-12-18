import { BadgeCheck, Info, Tag, ListChecks } from "lucide-react";

export default function SummaryCard({ summary }: { summary: any }) {
  if (!summary) return null;

  // Detect V6 format
  const isV6 =
    summary.judul ||
    summary.deskripsi ||
    summary.kategori ||
    summary.prioritas;

  // Detect V5 format (legacy)
  const isV5 = Array.isArray(summary.kriteria) && summary.kriteria.length > 0;

  // Extract unified data model (normalize to 1 shape)
  const data = isV6
    ? {
        id: summary.id || "",
        nama: summary.judul,
        deskripsi: summary.deskripsi,
        prioritas: summary.prioritas,
        kategori: summary.kategori,
        fitur_kunci: summary.fitur_kunci || [],
      }
    : isV5
    ? {
        id: summary.kriteria[0].id,
        nama: summary.kriteria[0].nama,
        deskripsi: summary.kriteria[0].deskripsi,
        prioritas: summary.kriteria[0].prioritas,
        kategori: summary.kriteria[0].kategori,
        fitur_kunci: [],
      }
    : null;

  if (!data) return null;

  return (
    <div className="space-y-6 text-gray-800">

      {/* HEADER */}
      <div className="flex items-center gap-3">
        <BadgeCheck className="w-6 h-6 text-blue-600" />
        <h2 className="text-xl font-bold tracking-tight text-gray-900">
          Requirement Summary
        </h2>
      </div>

      {/* TOP ROW — ID, PRIORITAS & KATEGORI */}
      <div className="grid grid-cols-3 gap-6">
        <div>
          <p className="text-xs text-gray-500 font-semibold">ID</p>
          <p className="text-base font-medium mt-1">{data.id || "—"}</p>
        </div>

        <div>
          <p className="text-xs text-gray-500 font-semibold">Prioritas</p>
          <span className="mt-1 inline-flex px-3 py-1 text-sm font-medium rounded-full 
                           bg-blue-50 text-blue-700 border border-blue-200">
            {data.prioritas || "—"}
          </span>
        </div>

        <div>
          <p className="text-xs text-gray-500 font-semibold">Kategori</p>
          <span className="mt-1 inline-flex px-3 py-1 text-sm font-medium rounded-full 
                           bg-gray-100 border text-gray-700">
            {data.kategori || "—"}
          </span>
        </div>
      </div>

      {/* NAMA FEATURE */}
      <div>
        <p className="text-xs text-gray-500 font-semibold">Nama Requirement</p>
        <p className="text-lg font-semibold mt-1">{data.nama}</p>
      </div>

      {/* DESKRIPSI */}
      <div>
        <p className="text-xs text-gray-500 font-semibold">Deskripsi</p>
        <div className="mt-2 bg-gray-50 rounded-lg border p-4 leading-relaxed text-[15px]">
          {data.deskripsi}
        </div>
      </div>

      {/* FITUR KUNCI (ONLY IF V6) */}
      {data.fitur_kunci?.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <ListChecks className="w-4 h-4 text-gray-600" />
            <span className="text-sm font-semibold text-gray-700">
              Fitur Kunci
            </span>
          </div>

          <ul className="ml-6 list-disc space-y-1">
            {data.fitur_kunci.map((item: string, i: number) => (
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
