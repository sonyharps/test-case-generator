/* ============================================
   PREMIUM TEST CASE ACCORDION (STABLE)
   - Anti blank
   - Anti crash
   - Safe for noisy LLM output
=============================================== */

type AnyTC = Record<string, any>;

const toArray = (v: any): any[] =>
  Array.isArray(v) ? v : v ? [v] : [];

export default function TCAccordion({ data }: { data?: any }) {
  // -----------------------------
  // HARD GUARD
  // -----------------------------
  if (!Array.isArray(data) || data.length === 0) {
    return (
      <p className="text-sm text-gray-500 italic">
        Tidak ada test case.
      </p>
    );
  }

  // -----------------------------
  // SAFE RENDER
  // -----------------------------
  try {
    return (
      <div className="space-y-4">
        {data
          .filter((tc: AnyTC) => tc && typeof tc === "object")
          .map((tc: AnyTC, idx: number) => {
            const tcId =
              typeof tc.tc_id === "string" ? tc.tc_id : `TC-${idx + 1}`;

            const title =
              typeof tc.title === "string" && tc.title.trim()
                ? tc.title
                : "Untitled Test Case";

            const preconditions = toArray(tc.preconditions);
            const steps = toArray(tc.steps);
            const expected = toArray(tc.expected_result);

            return (
              <div
                key={tcId}
                className="border border-gray-200 bg-white rounded-xl shadow-sm hover:shadow-md transition-all p-5"
              >
                {/* ================= HEADER ================= */}
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                      <span className="text-blue-700">{tcId}</span>
                      — {title}
                    </h3>

                    {/* BADGES */}
                    <div className="flex flex-wrap gap-2 mt-2">
                      {tcId.startsWith("TC-F") && (
                        <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded-md">
                          Functional
                        </span>
                      )}

                      {tcId.startsWith("TC-N") && (
                        <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-700 rounded-md">
                          Negative
                        </span>
                      )}

                      {tcId.startsWith("TC-B") && (
                        <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-md">
                          Boundary
                        </span>
                      )}

                      {typeof tc.boundary_type === "string" &&
                        tc.boundary_type.trim() && (
                          <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded-md">
                            {tc.boundary_type}
                          </span>
                        )}
                    </div>
                  </div>
                </div>

                <hr className="mb-4" />

                {/* ================= BODY ================= */}
                <div className="space-y-6">
                  {/* Preconditions */}
                  {preconditions.length > 0 && (
                    <div>
                      <div className="text-sm font-semibold mb-1 text-gray-900">
                        Preconditions
                      </div>
                      <ul className="list-disc ml-6 text-sm text-gray-700 space-y-1">
                        {preconditions.map((p, i) => (
                          <li key={i}>
                            {typeof p === "string"
                              ? p
                              : JSON.stringify(p)}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Steps */}
                  {steps.length > 0 && (
                    <div>
                      <div className="text-sm font-semibold mb-1 text-gray-900">
                        Steps
                      </div>
                      <ol className="list-decimal ml-6 text-sm text-gray-700 space-y-1">
                        {steps.map((s, i) => (
                          <li key={i}>
                            {typeof s === "string"
                              ? s
                              : JSON.stringify(s)}
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}

                  {/* Expected Result */}
                  {expected.length > 0 && (
                    <div>
                      <div className="text-sm font-semibold mb-1 text-gray-900">
                        Expected Result
                      </div>
                      <ul className="space-y-1 ml-1">
                        {expected.map((e, i) => (
                          <li
                            key={i}
                            className="flex items-start gap-2 text-sm text-gray-700"
                          >
                            <span className="text-green-600 mt-1">✔</span>
                            <span>
                              {typeof e === "string"
                                ? e
                                : JSON.stringify(e)}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
      </div>
    );
  } catch (err) {
    console.error("TCAccordion render error:", err);
    return (
      <div className="text-sm text-red-600">
        Gagal menampilkan test case.
      </div>
    );
  }
}
