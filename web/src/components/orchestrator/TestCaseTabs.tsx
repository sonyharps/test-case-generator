import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import TestCaseCard from "./TestCaseCard";

// type untuk test case per item
export type TestCaseItem = {
  tc_id: string;
  title: string;
  preconditions?: string[];
  steps?: string[];
  expected_result?: string[];
};

// type props keseluruhan tab
type TestCaseTabsProps = {
  functional: TestCaseItem[];
  negative: TestCaseItem[];
  boundary: TestCaseItem[];
};

export default function TestCaseTabs({
  functional,
  negative,
  boundary,
}: TestCaseTabsProps) {
  return (
    <Tabs defaultValue="functional" className="w-full">

      <TabsList>
        <TabsTrigger value="functional">Functional</TabsTrigger>
        <TabsTrigger value="negative">Negative</TabsTrigger>
        <TabsTrigger value="boundary">Boundary</TabsTrigger>
      </TabsList>

      {/* FUNCTIONAL */}
      <TabsContent value="functional">
        {functional.map((tc) => (
          <TestCaseCard
            key={tc.tc_id}
            tc={tc}
            intent="functional"
          />
        ))}
      </TabsContent>

      {/* NEGATIVE */}
      <TabsContent value="negative">
        {negative.map((tc) => (
          <TestCaseCard
            key={tc.tc_id}
            tc={tc}
            intent="negative"
          />
        ))}
      </TabsContent>

      {/* BOUNDARY */}
      <TabsContent value="boundary">
        {boundary.map((tc) => (
          <TestCaseCard
            key={tc.tc_id}
            tc={tc}
            intent="boundary"
          />
        ))}
      </TabsContent>

    </Tabs>
  );
}
