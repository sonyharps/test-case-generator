import { useEffect, useState } from "react";
import { listDocuments, type DocumentSummary } from "@/api/documents";
import { useAuth } from "@/store/auth.store";
import { useOrchestrator } from "@/store/orchestrator.store";

/**
 * Multi-select document picker for the V8 document-driven pipeline.
 * Lets the user pick several uploaded documents (PRD + user stories + Figma
 * flow, etc.) to feed to the LLM as a single rich, mixed context.
 * If no document is selected, the orchestrator runs the legacy V7 free-text flow.
 */
export default function DocumentPicker() {
  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const token = useAuth((s) => s.accessToken);
  const { selectedDocumentIds, toggleDocumentId } = useOrchestrator();

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    listDocuments(token)
      .then((res) => {
        if (cancelled) return;
        const ready = (res.documents || []).filter((d) => d.processing_status === "completed");
        setDocs(ready);
        setError(null);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : "Failed to load documents");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700">
          Generate dari dokumen (multi-select, opsional)
        </label>
        <span className="text-xs text-gray-400">
          {docs.length} dokumen tersedia · {selectedDocumentIds.length} dipilih
        </span>
      </div>

      {loading ? (
        <p className="text-sm text-gray-400">Memuat dokumen...</p>
      ) : error ? (
        <p className="text-sm text-red-500">{error}</p>
      ) : docs.length === 0 ? (
        <p className="text-sm text-gray-400 italic">
          Belum ada dokumen. Upload PRD/user story/diagram di menu Dokumen untuk
          memakai pipeline multi-dokumen.
        </p>
      ) : (
        <div className="space-y-1.5 max-h-48 overflow-y-auto">
          {docs.map((d) => {
            const checked = selectedDocumentIds.includes(d.id);
            return (
              <label
                key={d.id}
                className={`flex items-center gap-2.5 p-2 rounded-md cursor-pointer transition-colors ${
                  checked ? "bg-blue-50 border border-blue-200" : "hover:bg-gray-50 border border-transparent"
                }`}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggleDocumentId(d.id)}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm flex-1 truncate">
                  {d.title || d.filename}
                </span>
                <span className="text-xs text-gray-400 shrink-0">
                  {d.requirement_count > 0 ? `${d.requirement_count} req` : ""}
                </span>
              </label>
            );
          })}
        </div>
      )}

      {selectedDocumentIds.length > 0 && (
        <p className="mt-2 text-xs text-blue-600">
          Mode multi-dokumen aktif: {selectedDocumentIds.length} dokumen akan
          dibaca bersama untuk menghasilkan test case yang lebih kaya.
        </p>
      )}
    </div>
  );
}
