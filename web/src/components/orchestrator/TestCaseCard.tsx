// src/components/orchestrator/TestCaseCard.tsx

import type { TestCase } from "@/types/orchestrator";
import { Card, CardContent } from "@/components/ui/card";

interface Props {
  tc: TestCase;
  intent: "functional" | "negative" | "boundary";
}

export default function TestCaseCard({ tc, intent }: Props) {
  const badgeColor =
    intent === "functional"
      ? "bg-blue-100 text-blue-700"
      : intent === "negative"
      ? "bg-red-100 text-red-700"
      : "bg-purple-100 text-purple-700";

  return (
    <Card className="border rounded-lg shadow-sm">
      <CardContent className="p-4 space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-md font-semibold">
            {tc.tc_id} — {tc.title}
          </h3>
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${badgeColor}`}>
            {intent}
          </span>
        </div>

        {tc.preconditions?.length > 0 && (
          <p className="text-sm text-gray-600">
            <b>Preconditions:</b> {tc.preconditions.join(", ")}
          </p>
        )}

        {tc.steps?.length > 0 && (
          <p className="text-sm text-gray-600">
            <b>Steps:</b> {tc.steps.join(", ")}
          </p>
        )}

        {tc.expected_result?.length > 0 && (
          <p className="text-sm text-gray-600">
            <b>Expected:</b> {tc.expected_result.join(", ")}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
