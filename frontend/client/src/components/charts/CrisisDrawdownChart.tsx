import { Card } from "@/components/ui/card";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface CrisisDrawdownData {
  date: number;
  gfc2008: number;
  covid2020: number;
  taper2013: number;
  hike2022: number;
}

interface CrisisDrawdownChartProps {
  data: CrisisDrawdownData[];
}

export default function CrisisDrawdownChart({
  data,
}: CrisisDrawdownChartProps) {
  return (
    <Card className="bg-card border-border/50 p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold">Crisis Drawdown Curves</h3>
        <p className="text-xs text-muted-foreground mt-1">
          Historical replay through major market crises
        </p>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis
            dataKey="date"
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
          />
          <YAxis
            tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "0.5rem",
            }}
            labelStyle={{ color: "hsl(var(--foreground))" }}
            formatter={(value: number) => `${(value * 100).toFixed(2)}%`}
          />
          <Legend wrapperStyle={{ color: "hsl(var(--muted-foreground))" }} />
          <Line
            type="monotone"
            dataKey="gfc2008"
            stroke="#ef4444"
            dot={false}
            strokeWidth={2}
            name="GFC 2008"
          />
          <Line
            type="monotone"
            dataKey="covid2020"
            stroke="#f97316"
            dot={false}
            strokeWidth={2}
            name="COVID 2020"
          />
          <Line
            type="monotone"
            dataKey="taper2013"
            stroke="#eab308"
            dot={false}
            strokeWidth={2}
            name="Taper 2013"
          />
          <Line
            type="monotone"
            dataKey="hike2022"
            stroke="#d4af37"
            dot={false}
            strokeWidth={2}
            name="Rate Hike 2022"
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}
