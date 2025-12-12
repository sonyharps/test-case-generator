import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface Props {
  level: "Low" | "Medium" | "High" | string;
  notes?: string[];
}

export default function RiskMeter({ level, notes = [] }: Props) {
  // Warna otomatis berdasar level
  const levelColor = {
    Low: "bg-blue-200 text-blue-700 border-blue-300",
    Medium: "bg-orange-200 text-orange-700 border-orange-300",
    High: "bg-purple-200 text-purple-700 border-purple-300",
  }[level] || "bg-gray-200 text-gray-700 border-gray-300";

  // Bar range otomatis
  const barWidth = {
    Low: "w-1/5 bg-blue-500",
    Medium: "w-3/5 bg-orange-500",
    High: "w-full bg-purple-500",
  }[level] || "w-1/5 bg-gray-500";

  return (
    <Card className="rounded-xl shadow-sm border border-gray-200">
      <CardContent className="p-4 space-y-3">
        <div className="flex justify-between items-center">
          <p className="text-sm font-medium text-gray-700">Risk Level</p>
          <span
            className={cn(
              "px-3 py-1 text-xs rounded-full border",
              levelColor
            )}
          >
            {level}
          </span>
        </div>

        {/* Risk meter bar */}
        <div className="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
          <div className={cn("h-full rounded-full transition-all", barWidth)} />
        </div>

        {/* Notes */}
        {notes.length > 0 && (
          <div className="mt-2">
            <p className="text-xs font-medium text-gray-700 mb-1">Notes:</p>
            <ul className="text-xs text-gray-600 list-disc list-inside space-y-1">
              {notes.map((note, i) => (
                <li key={i}>{note}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
