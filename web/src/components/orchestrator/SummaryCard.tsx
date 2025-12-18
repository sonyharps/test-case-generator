export default function SummaryCard({ summary }: { summary: any }) {
  if (!summary?.kriteria?.length) return null;

  const item = summary.kriteria[0];

  return (
    <div className="space-y-4 text-sm text-gray-800 leading-relaxed">

      <div>
        <span className="font-semibold text-gray-900">ID:</span>
        <span className="ml-2">{item.id}</span>
      </div>

      <div>
        <span className="font-semibold text-gray-900">Nama:</span>
        <span className="ml-2">{item.nama}</span>
      </div>

      <div>
        <span className="font-semibold text-gray-900">Deskripsi:</span>
        <p className="ml-2 mt-1 bg-gray-50 p-3 rounded-lg border">
          {item.deskripsi}
        </p>
      </div>

      <div className="flex gap-4">
        <div>
          <span className="font-semibold text-gray-900">Prioritas:</span>
          <span className="ml-2">{item.prioritas}</span>
        </div>
        <div>
          <span className="font-semibold text-gray-900">Kategori:</span>
          <span className="ml-2">{item.kategori}</span>
        </div>
      </div>

    </div>
  );
}
