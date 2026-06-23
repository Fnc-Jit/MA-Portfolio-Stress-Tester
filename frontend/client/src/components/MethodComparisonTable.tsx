import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertCircle } from "lucide-react";
export interface MethodComparison {
  metric: string;
  historical: number;
  parametric: number;
  monteCarlo: number;
  factorShock: number;
  agreement: "high" | "medium" | "low";
}

interface MethodComparisonTableProps {
  data: MethodComparison[];
}

export default function MethodComparisonTable({
  data,
}: MethodComparisonTableProps) {
  const formatValue = (value: number, metric: string): string => {
    if (metric.includes("Ratio")) {
      return value.toFixed(3);
    } else if (metric.includes("Vol")) {
      return `${(value * 100).toFixed(2)}%`;
    }
    return `$${(value / 1000).toFixed(1)}k`;
  };

  const getAgreementColor = (agreement: string) => {
    switch (agreement) {
      case "high":
        return "bg-green-500/20 text-green-400 border-green-500/30";
      case "medium":
        return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
      case "low":
        return "bg-red-500/20 text-red-400 border-red-500/30";
      default:
        return "";
    }
  };

  return (
    <Card className="bg-card border-border/50 p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-2">Method Comparison</h3>
        <p className="text-xs text-muted-foreground">
          Cross-validation of risk metrics across four independent models
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border/50">
              <th className="text-left p-3 text-muted-foreground font-medium">
                Metric
              </th>
              <th className="text-right p-3 text-muted-foreground font-medium">
                Historical
              </th>
              <th className="text-right p-3 text-muted-foreground font-medium">
                Parametric
              </th>
              <th className="text-right p-3 text-muted-foreground font-medium">
                Monte Carlo
              </th>
              <th className="text-right p-3 text-muted-foreground font-medium">
                Factor Shock
              </th>
              <th className="text-center p-3 text-muted-foreground font-medium">
                Agreement
              </th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => (
              <tr
                key={idx}
                className="border-b border-border/30 hover:bg-accent/5 transition-colors"
              >
                <td className="p-3 font-medium text-foreground">{row.metric}</td>
                <td className="p-3 text-right numeric text-muted-foreground">
                  {formatValue(row.historical, row.metric)}
                </td>
                <td className="p-3 text-right numeric text-accent font-semibold">
                  {formatValue(row.parametric, row.metric)}
                </td>
                <td className="p-3 text-right numeric text-muted-foreground">
                  {formatValue(row.monteCarlo, row.metric)}
                </td>
                <td className="p-3 text-right numeric text-muted-foreground">
                  {formatValue(row.factorShock, row.metric)}
                </td>
                <td className="p-3 text-center">
                  <Badge
                    className={`${getAgreementColor(
                      row.agreement
                    )} border gap-1 font-medium`}
                  >
                    {row.agreement === "low" && (
                      <AlertCircle className="w-3 h-3" />
                    )}
                    {row.agreement.charAt(0).toUpperCase() + row.agreement.slice(1)}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Methodology Notes */}
      <div className="mt-6 p-4 bg-accent/5 border border-accent/20 rounded-lg text-xs text-muted-foreground space-y-2">
        <p className="font-medium text-foreground">Methodology Notes:</p>
        <ul className="space-y-1 ml-4 list-disc">
          <li>
            <strong>Historical:</strong> Crisis window replay from 2005-present
          </li>
          <li>
            <strong>Parametric:</strong> Normal distribution VaR using 2Y covariance
          </li>
          <li>
            <strong>Monte Carlo:</strong> 10,000 Cholesky-decomposed simulations
          </li>
          <li>
            <strong>Factor Shock:</strong> Macro factor beta regression + shock impact
          </li>
        </ul>
      </div>
    </Card>
  );
}
