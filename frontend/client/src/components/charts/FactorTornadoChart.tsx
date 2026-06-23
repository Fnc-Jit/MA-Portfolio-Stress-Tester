import { Card } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface FactorTornadoData {
  factor: string;
  impact: number;
}

interface FactorTornadoChartProps {
  data: FactorTornadoData[];
}

export default function FactorTornadoChart({
  data,
}: FactorTornadoChartProps) {
  // Sort by absolute impact
  const sortedData = [...data].sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact));

  return (
    <Card className="bg-card border-border/50 p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold">Factor Sensitivity Tornado</h3>
        <p className="text-xs text-muted-foreground mt-1">
          Portfolio impact under macro factor shocks
        </p>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={sortedData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 200, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis
            type="number"
            tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
            tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
          />
          <YAxis
            dataKey="factor"
            type="category"
            tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
            width={190}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "var(--card)",
              border: "1px solid var(--border)",
              borderRadius: "0.5rem",
            }}
            labelStyle={{ color: "var(--foreground)" }}
            formatter={(value: number) => `$${value.toFixed(0)}`}
          />
          <Bar
            dataKey="impact"
            fill="var(--accent)"
            radius={[0, 4, 4, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}
