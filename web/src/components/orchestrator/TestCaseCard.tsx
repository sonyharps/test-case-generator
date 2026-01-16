// Helper to ensure value is always an array
function ensureArray(value: any): string[] {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  if (typeof value === "string") return [value];
  return [];
}

export default function TestCaseCard({ tc }: { tc: any }) {
  if (!tc) return null;

  const preconditions = ensureArray(tc.preconditions);
  const steps = ensureArray(tc.steps);
  const expectedResults = ensureArray(tc.expected_result);

  return (
    <div className="border rounded-lg p-4 space-y-3 bg-white">

      {/* HEADER */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono text-gray-500">
          {tc.tc_id}
        </span>
        <h3 className="font-semibold text-gray-900">
          {tc.title || "Untitled Test Case"}
        </h3>
      </div>

      {/* PRECONDITIONS */}
      {preconditions.length > 0 && (
        <div>
          <p className="text-sm font-semibold text-gray-700">Preconditions</p>
          <ul className="list-disc ml-6 text-sm text-gray-600">
            {preconditions.map((p: string, i: number) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        </div>
      )}

      {/* STEPS */}
      {steps.length > 0 && (
        <div>
          <p className="text-sm font-semibold text-gray-700">Steps</p>
          <ol className="list-decimal ml-6 text-sm text-gray-600">
            {steps.map((s: string, i: number) => (
              <li key={i}>{s}</li>
            ))}
          </ol>
        </div>
      )}

      {/* EXPECTED RESULT */}
      {expectedResults.length > 0 && (
        <div>
          <p className="text-sm font-semibold text-gray-700">Expected Result</p>
          <ul className="list-disc ml-6 text-sm text-gray-600">
            {expectedResults.map((e: string, i: number) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        </div>
      )}

    </div>
  );
}
