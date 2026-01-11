export default function CoverageCard({
  functional,
  negative,
  boundary,
}: {
  functional: number;
  negative: number;
  boundary: number;
}) {
  return (
    <div className="border rounded-xl p-4 bg-blue-50">
      <h3 className="font-semibold text-blue-700 mb-2">
        Test Coverage Summary
      </h3>
      <ul className="list-disc ml-5 text-sm text-blue-800">
        <li>Functional : {functional}</li>
        <li>Negative : {negative}</li>
        <li>Boundary : {boundary}</li>
      </ul>
    </div>
  );
}
