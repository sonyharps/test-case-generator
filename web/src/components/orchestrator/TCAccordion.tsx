import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";

import type { TestCase } from "@/types/orchestrator";

interface Props {
  title: string;
  data: TestCase[];
}

export default function TCAccordion({ title, data }: Props) {
  return (
    <div className="border rounded-xl p-4 shadow-sm bg-white">
      <h2 className="text-lg font-semibold mb-3">{title}</h2>

      <Accordion type="single" collapsible className="w-full space-y-2">
        {data.map((tc) => (
          <AccordionItem key={tc.tc_id} value={tc.tc_id}>
            <AccordionTrigger className="text-left">
              <span className="font-medium">{tc.tc_id} — {tc.title}</span>
            </AccordionTrigger>

            <AccordionContent className="text-sm space-y-2">
              {tc.preconditions.length > 0 && (
                <div>
                  <strong>Preconditions:</strong> {tc.preconditions.join(", ")}
                </div>
              )}

              {tc.steps.length > 0 && (
                <div>
                  <strong>Steps:</strong>
                  <ul className="list-disc pl-5">
                    {tc.steps.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}

              {tc.expected_result.length > 0 && (
                <div>
                  <strong>Expected:</strong> {tc.expected_result.join(", ")}
                </div>
              )}
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  );
}
