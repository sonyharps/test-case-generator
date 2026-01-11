export default function TestCaseCard({ tc }: { tc: any }) {
  if (!tc) return null;

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
      <div>
        <p className="text-sm font-semibold text-gray-700">Preconditions</p>
        <ul className="list-disc ml-6 text-sm text-gray-600">
          {(tc.preconditions || []).map((p: string, i: number) => (
            <li key={i}>{p}</li>
          ))}
        </ul>
      </div>

      {/* STEPS */}
      <div>
        <p className="text-sm font-semibold text-gray-700">Steps</p>
        <ol className="list-decimal ml-6 text-sm text-gray-600">
          {(tc.steps || []).map((s: string, i: number) => (
            <li key={i}>{s}</li>
          ))}
        </ol>
      </div>

      {/* EXPECTED RESULT */}
      <div>
        <p className="text-sm font-semibold text-gray-700">Expected Result</p>
        <ul className="list-disc ml-6 text-sm text-gray-600">
          {(tc.expected_result || []).map((e: string, i: number) => (
            <li key={i}>{e}</li>
          ))}
        </ul>
      </div>

    </div>
  );
}
