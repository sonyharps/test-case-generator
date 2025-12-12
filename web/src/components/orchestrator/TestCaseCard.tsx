type TestCaseCardProps = {
  tc: {
    tc_id: string;
    title: string;
    preconditions?: string[];
    steps?: string[];
    expected_result?: string[];
  };
  intent: "functional" | "negative" | "boundary"; // atau string kalau fleksibel
};


export default function TestCaseCard({ tc, intent }: TestCaseCardProps) {
  return (
    <div className="p-5 my-4 bg-white border rounded-xl shadow-sm">
      <div className="flex justify-between">
        <h3 className="font-semibold">{tc.tc_id} — {tc.title}</h3>
        <span className="text-sm px-3 py-1 rounded-full bg-blue-100 text-blue-600">{intent}</span>
      </div>

      {(tc.preconditions?.length ?? 0) > 0 && (
        <p className="mt-2 text-sm"><b>Preconditions:</b> {(tc.preconditions ?? []).join(", ")}</p>
      )}

      {(tc.steps?.length ?? 0) > 0 && (
        <p className="mt-2 text-sm"><b>Steps:</b> {(tc.steps ?? []).join(", ")}</p>
      )}

      {(tc.expected_result?.length ?? 0) > 0 && (
        <p className="mt-2 text-sm"><b>Expected:</b> {(tc.expected_result ?? []).join(", ")}</p>
      )}
    </div>
  );
}
