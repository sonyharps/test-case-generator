import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  summary: string;
}

export default function OrchestratorSummary({ summary }: Props) {
  return (
    <Card className="border-blue-100 shadow-sm rounded-xl">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-blue-700">
          Requirement under test
        </CardTitle>
      </CardHeader>

      <CardContent>
        <p className="text-gray-700 whitespace-pre-line">
          {summary || "No requirement provided yet."}
        </p>

        <p className="text-xs text-gray-500 mt-3">
          Tips: requirement ini nanti dikirim ke endpoint Orchestrator API.
        </p>
      </CardContent>
    </Card>
  );
}
