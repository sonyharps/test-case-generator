import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import TestCaseCard from "./TestCaseCard";

type TestCase = {
  tc_id: string;
  title: string;
  preconditions?: string[];
  steps?: string[];
  expected_result?: string[];
};

type Props = {
  functional?: TestCase[];
  negative?: TestCase[];
  boundary?: TestCase[];
};

function EmptyState({ label }: { label: string }) {
  return (
    <div className="text-sm text-gray-400 italic py-4">
      Tidak ada test case {label}.
    </div>
  );
}

export default function TestCaseTabs({
  functional = [],
  negative = [],
  boundary = [],
}: Props) {
  return (
    <Tabs defaultValue="functional" className="w-full">

      <TabsList>
        <TabsTrigger value="functional">
          Functional ({functional.length})
        </TabsTrigger>
        <TabsTrigger value="negative">
          Negative ({negative.length})
        </TabsTrigger>
        <TabsTrigger value="boundary">
          Boundary ({boundary.length})
        </TabsTrigger>
      </TabsList>

      <TabsContent value="functional" className="space-y-4">
        {functional.length === 0 ? (
          <EmptyState label="functional" />
        ) : (
          functional.map((tc) => (
            <TestCaseCard key={tc.tc_id} tc={tc} />
          ))
        )}
      </TabsContent>

      <TabsContent value="negative" className="space-y-4">
        {negative.length === 0 ? (
          <EmptyState label="negative" />
        ) : (
          negative.map((tc) => (
            <TestCaseCard key={tc.tc_id} tc={tc} />
          ))
        )}
      </TabsContent>

      <TabsContent value="boundary" className="space-y-4">
        {boundary.length === 0 ? (
          <EmptyState label="boundary" />
        ) : (
          boundary.map((tc) => (
            <TestCaseCard key={tc.tc_id} tc={tc} />
          ))
        )}
      </TabsContent>

    </Tabs>
  );
}
