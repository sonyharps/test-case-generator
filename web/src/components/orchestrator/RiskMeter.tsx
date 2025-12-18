import {
  RadialBarChart,
  RadialBar,
  ResponsiveContainer,
  PolarAngleAxis,
} from "recharts";

interface Props {
  level: string;
}

export default function RiskMeter({ level }: Props) {
  // Mapping risk → numeric %
  const map: Record<string, number> = {
    Low: 20,
    Medium: 50,
    High: 80,
    Critical: 100,
  };

  const value = map[level] ?? 0;

  const data = [
    {
      name: "risk",
      value,
      fill:
        value < 40 ? "#3b82f6" : value < 70 ? "#f97316" : value < 100 ? "#a855f7" : "#ef4444",
    },
  ];

  return (
    <div className="flex flex-col items-center p-2">
      <div className="text-sm font-medium text-gray-600 mb-2">
        Risk Level: {level}
      </div>

      <ResponsiveContainer width={150} height={150}>
        <RadialBarChart
          innerRadius="60%"
          outerRadius="100%"
          data={data}
          startAngle={180}
          endAngle={0}
        >
          <PolarAngleAxis
            type="number"
            domain={[0, 100]}
            tick={false}
          />
          <RadialBar
            dataKey="value"
            cornerRadius={10}
            background={{
              fill: "#e5e7eb",
            }}
          />
        </RadialBarChart>
      </ResponsiveContainer>

      <div className="text-xs text-gray-500 mt-1">Risk Score: {value}%</div>
    </div>
  );
}
