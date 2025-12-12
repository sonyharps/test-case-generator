import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type CoverageMatrix = {
  functional_count?: number;
  negative_count?: number;
  boundary_count?: number;
};

interface Props {
  data?: CoverageMatrix | null;
}

export default function CoverageStats({ data }: Props) {
  const cov = data ?? { functional_count: 0, negative_count: 0, boundary_count: 0 };

  const total =
    (cov.functional_count ?? 0) +
    (cov.negative_count ?? 0) +
    (cov.boundary_count ?? 0);

  return (
    <Card className="border-blue-100 shadow-sm rounded-xl">
      <CardHeader>
        <CardTitle className="text-base font-semibold text-slate-700">
          Coverage Matrix
        </CardTitle>
      </CardHeader>

      <CardContent>
        <div className="grid grid-cols-3 gap-3">
          <div className="p-4 bg-white rounded-lg shadow-sm text-center">
            <div className="text-2xl font-bold text-blue-600">{cov.functional_count ?? 0}</div>
            <div className="text-xs text-slate-500">Functional</div>
          </div>

          <div className="p-4 bg-white rounded-lg shadow-sm text-center">
            <div className="text-2xl font-bold text-amber-500">{cov.negative_count ?? 0}</div>
            <div className="text-xs text-slate-500">Negative</div>
          </div>

          <div className="p-4 bg-white rounded-lg shadow-sm text-center">
            <div className="text-2xl font-bold text-violet-500">{cov.boundary_count ?? 0}</div>
            <div className="text-xs text-slate-500">Boundary</div>
          </div>
        </div>

        <div className="mt-4 text-sm text-slate-600">
          Total: <span className="font-medium">{total}</span>
        </div>
      </CardContent>
    </Card>
  );
}