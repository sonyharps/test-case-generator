// src/components/orchestrator/TestCaseTabs.tsx
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "@/components/ui/tabs";

import TestCaseCard from "./TestCaseCard";
import type { TestCase } from "@/types/orchestrator";

interface Props {
  functional: TestCase[];
  negative: TestCase[];
  boundary: TestCase[];
}

export default function TestCaseTabs({ functional, negative, boundary }: Props) {
  return (
    <Tabs defaultValue="functional" className="w-full">
      <TabsList className="mb-4 w-full flex justify-start">
        <TabsTrigger value="functional">Functional</TabsTrigger>
        <TabsTrigger value="negative">Negative</TabsTrigger>
        <TabsTrigger value="boundary">Boundary</TabsTrigger>
      </TabsList>

      {/* Functional */}
      <TabsContent value="functional">
        <div className="space-y-4">
          {functional.map((tc) => (
            <TestCaseCard key={tc.tc_id} tc={tc} intent="functional" />
          ))}
        </div>
      </TabsContent>

      {/* Negative */}
      <TabsContent value="negative">
        <div className="space-y-4">
          {negative.map((tc) => (
            <TestCaseCard key={tc.tc_id} tc={tc} intent="negative" />
          ))}
        </div>
      </TabsContent>

      {/* Boundary */}
      <TabsContent value="boundary">
        <div className="space-y-4">
          {boundary.map((tc) => (
            <TestCaseCard key={tc.tc_id} tc={tc} intent="boundary" />
          ))}
        </div>
      </TabsContent>
    </Tabs>
  );
}
