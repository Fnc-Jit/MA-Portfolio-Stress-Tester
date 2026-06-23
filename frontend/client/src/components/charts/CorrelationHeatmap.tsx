import { Card } from "@/components/ui/card";

interface CorrelationHeatmapProps {
  data: number[][];
  tickers?: string[];
}

export default function CorrelationHeatmap({ data, tickers }: CorrelationHeatmapProps) {
  const assetNames = tickers && tickers.length === data.length 
    ? tickers 
    : Array.from({ length: data.length }, (_, i) => `Asset ${i + 1}`);

  // Function to get color based on correlation value
  const getColor = (value: number): string => {
    // Red for negative, white/transparent for 0, gold/accent for positive correlation
    if (value < 0) {
      return `rgba(239, 68, 68, ${Math.abs(value) * 0.6})`;
    } else if (value > 0) {
      return `rgba(212, 175, 55, ${value * 0.6})`;
    }
    return "rgba(255, 255, 255, 0.05)";
  };

  return (
    <Card className="bg-card border-border/50 p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold">Correlation Matrix</h3>
        <p className="text-xs text-muted-foreground mt-1">
          Historical asset correlation heatmap
        </p>
      </div>

      <div className="overflow-x-auto">
        {data.length === 0 ? (
          <div className="h-[200px] flex items-center justify-center text-sm text-muted-foreground">
            No correlation data available.
          </div>
        ) : (
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr>
                <th className="text-left p-2 text-muted-foreground font-medium text-xs"></th>
                {assetNames.map((name, idx) => (
                  <th
                    key={idx}
                    className="text-center p-2 text-muted-foreground font-medium text-xs"
                  >
                    {name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, rowIdx) => (
                <tr key={rowIdx} className="hover:bg-accent/5">
                  <td className="text-left p-2 text-muted-foreground font-medium text-xs border-b border-border/30">
                    {assetNames[rowIdx]}
                  </td>
                  {row.map((value, colIdx) => (
                    <td
                      key={colIdx}
                      className="text-center p-2 numeric font-semibold text-xs border-b border-border/30"
                      style={{
                        backgroundColor: getColor(value),
                        color: value === 1 ? "hsl(var(--accent))" : "hsl(var(--foreground))",
                        transition: "background-color 0.2s ease",
                      }}
                    >
                      {value.toFixed(2)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Legend */}
      <div className="mt-6 flex items-center justify-center gap-6 text-xs">
        <div className="flex items-center gap-2">
          <div
            className="w-3.5 h-3.5 rounded"
            style={{ backgroundColor: "rgba(239, 68, 68, 0.5)" }}
          ></div>
          <span className="text-muted-foreground">Negative (-1.0)</span>
        </div>
        <div className="flex items-center gap-2">
          <div
            className="w-3.5 h-3.5 rounded border border-border/50"
            style={{ backgroundColor: "rgba(255, 255, 255, 0.05)" }}
          ></div>
          <span className="text-muted-foreground">Uncorrelated (0.0)</span>
        </div>
        <div className="flex items-center gap-2">
          <div
            className="w-3.5 h-3.5 rounded"
            style={{ backgroundColor: "rgba(212, 175, 55, 0.5)" }}
          ></div>
          <span className="text-muted-foreground">Positive (+1.0)</span>
        </div>
      </div>
    </Card>
  );
}
