import { Card } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface PnLPoint {
  range: string;
  normal: number;
  student_t: number;
}

interface PnLDistributionChartProps {
  data: PnLPoint[];
}

export default function PnLDistributionChart({ data }: PnLDistributionChartProps) {
  return (
    <Card className="bg-card border-border/50 p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold">PnL Distribution (Simulated)</h3>
        <p className="text-xs text-muted-foreground mt-1">
          Normal vs. Student-t (Fat-Tail df=5) simulation frequency
        </p>
      </div>
      
      {data.length === 0 ? (
        <div className="h-[300px] flex items-center justify-center text-sm text-muted-foreground">
          No simulation data available.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="range"
              tick={{ fill: "var(--muted-foreground)", fontSize: 9 }}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--card)",
                border: "1px solid var(--border)",
                borderRadius: "0.5rem",
              }}
              labelStyle={{ color: "var(--foreground)", fontSize: 12 }}
              itemStyle={{ fontSize: 12 }}
            />
            <Legend wrapperStyle={{ color: "var(--muted-foreground)", fontSize: 12 }} />
            <Bar
              dataKey="normal"
              fill="rgba(212, 175, 55, 0.4)"
              stroke="var(--accent)"
              strokeWidth={1.5}
              name="Normal MC"
              radius={[2, 2, 0, 0]}
            />
            <Bar
              dataKey="student_t"
              fill="rgba(239, 68, 68, 0.4)"
              stroke="#ef4444"
              strokeWidth={1.5}
              name="Student-t MC (Fat Tail)"
              radius={[2, 2, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
