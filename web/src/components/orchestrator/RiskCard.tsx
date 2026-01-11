export default function RiskCard({ risk }: { risk: any }) {
  if (!risk) return null;

  return (
    <div className="border rounded-xl p-4 bg-red-50">
      <h3 className="font-semibold text-red-700 mb-2">
        Risk Assessment: {risk.level}
      </h3>
      <ul className="list-disc ml-5 text-sm text-red-800">
        {risk.notes?.map((n: string, i: number) => (
          <li key={i}>{n}</li>
        ))}
      </ul>
    </div>
  );
}
