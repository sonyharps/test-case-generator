import { Skeleton } from "@/components/ui/skeleton";

export default function OrchestratorSkeleton() {
  return (
    <div className="space-y-6">
      {/* Summary Skeleton */}
      <div className="p-6 border rounded-xl bg-white">
        <Skeleton className="h-6 w-48 mb-4" />
        <Skeleton className="h-4 w-full mb-2" />
        <Skeleton className="h-4 w-3/4" />
      </div>

      {/* Coverage + Risk + Metadata */}
      <div className="grid grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="p-6 border rounded-xl bg-white">
            <Skeleton className="h-5 w-40 mb-4" />
            <Skeleton className="h-4 w-20 mb-2" />
            <Skeleton className="h-4 w-28 mb-1" />
            <Skeleton className="h-4 w-16" />
          </div>
        ))}
      </div>

      {/* Test Cases Skeleton */}
      <div className="p-6 border rounded-xl bg-white">
        <Skeleton className="h-5 w-60 mb-4" />
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="mb-4">
            <Skeleton className="h-4 w-48 mb-2" />
            <Skeleton className="h-4 w-96" />
          </div>
        ))}
      </div>
    </div>
  );
}
