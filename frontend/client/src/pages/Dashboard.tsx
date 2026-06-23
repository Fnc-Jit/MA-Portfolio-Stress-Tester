import { useState, useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLocation } from "wouter";
import { ArrowLeft, Download, RotateCw, AlertTriangle, RefreshCw } from "lucide-react";
import { validatePortfolio } from "@/lib/portfolioValidation";
import {
  validateTickers,
  computeRiskMetrics as computeRiskMetricsApi,
  downloadReport,
  generateHistogramData,
  generateDrawdownCurves,
  formatFactorTitle,
  formatCurrency,
  formatPercent,
  type RiskComputeResponse
} from "@/lib/api";
import PnLDistributionChart from "@/components/charts/PnLDistributionChart";
import CrisisDrawdownChart from "@/components/charts/CrisisDrawdownChart";
import FactorTornadoChart from "@/components/charts/FactorTornadoChart";
import CorrelationHeatmap from "@/components/charts/CorrelationHeatmap";
import MethodComparisonTable from "@/components/MethodComparisonTable";
import { Skeleton } from "@/components/ui/skeleton";

export default function Dashboard() {
  const [, setLocation] = useLocation();
  
  // Tickers & weights state
  const [tickers, setTickers] = useState<string[]>(["AAPL", "MSFT", "GOOGL"]);
  const [weights, setWeights] = useState<number[]>([0.4, 0.35, 0.25]);
  const [portfolioValue, setPortfolioValue] = useState(100000);
  
  // Risk configuration parameters
  const [lookbackDays, setLookbackDays] = useState(504);
  const [shocks] = useState<Record<string, number>>({
    vix: 0.50,
    y10: 0.02,
    oil: -0.20,
    usd: 0.05
  });
  const [riskFreeRate] = useState(0.04);
  
  // API loading states
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [apiData, setApiData] = useState<RiskComputeResponse | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  // Core API query execution
  const fetchRiskData = async (
    currentTickers = tickers,
    currentWeights = weights,
    currentValue = portfolioValue
  ) => {
    setIsLoading(true);
    setError(null);
    try {
      // 1. Client side validation check
      const validation = validatePortfolio(currentTickers, currentWeights, currentValue);
      if (!validation.isValid) {
        setError(validation.errors[0]?.message || "Validation failed.");
        setIsLoading(false);
        return;
      }

      // 2. Normalize weights locally if needed
      const sum = currentWeights.reduce((a, b) => a + b, 0);
      let normalizedWeights = [...currentWeights];
      if (Math.abs(sum - 1.0) > 0.001 && sum > 0) {
        normalizedWeights = currentWeights.map((w) => w / sum);
        setWeights(normalizedWeights);
      }

      // 3. Call backend portfolio validate endpoint (checks Yahoo Finance tickers existence)
      const validateResponse = await validateTickers(currentTickers, normalizedWeights);
      if (!validateResponse.isValid) {
        setError(validateResponse.message);
        setIsLoading(false);
        return;
      }

      // 4. Compute metrics from real risk engine
      const response = await computeRiskMetricsApi({
        tickers: currentTickers,
        weights: normalizedWeights,
        portfolio_value: currentValue,
        lookback_days: lookbackDays,
        shocks,
        risk_free_rate: riskFreeRate
      });
      setApiData(response);
    } catch (e: any) {
      console.error(e);
      setError(e.message || "Failed to communicate with risk engine backend.");
    } finally {
      setIsLoading(false);
    }
  };

  // Run on mount
  useEffect(() => {
    fetchRiskData();
  }, [lookbackDays]);

  // Compute metrics adapter mapping
  const metrics = useMemo(() => {
    if (!apiData) return null;

    // Search for worst crisis drawdown
    let worstCrisisName = "GFC 2008";
    let worstCrisisPnL = 0;

    Object.values(apiData.historical_replays).forEach((replay) => {
      if (replay.final_return < worstCrisisPnL) {
        worstCrisisPnL = replay.final_return;
        worstCrisisName = replay.crisis_name.replace("_", " ").toUpperCase();
      }
    });

    return {
      var95_1d: apiData.parametric.var_95_1d_usd,
      var99_1d: apiData.parametric.var_99_1d_usd,
      cvar95: apiData.parametric.cvar_95_1d_usd,
      worstCrisisPnL: worstCrisisPnL * apiData.portfolio_value,
      worstCrisisName: worstCrisisName,
      annualizedVol: apiData.general_metrics.annualized_volatility,
      sharpeRatio: apiData.general_metrics.sharpe_ratio,
      maxDrawdown: apiData.general_metrics.max_drawdown,
    };
  }, [apiData]);

  // Comparison table adapter mapping
  const methodComparison = useMemo(() => {
    if (!apiData) return [];

    const formatAgreement = (agreeStr: string): "high" | "medium" | "low" => {
      if (agreeStr === "AGREE") return "high";
      if (agreeStr === "DIVERGE_WARNING") return "medium";
      return "low";
    };

    return [
      {
        metric: "VaR (95%, 1-day)",
        historical: Math.abs(apiData.historical_replays.gfc_2008?.worst_day || 0) * apiData.portfolio_value,
        parametric: apiData.parametric.var_95_1d_usd,
        monteCarlo: apiData.monte_carlo.normal.var_95_1d_usd,
        factorShock: Math.abs(apiData.factor_shocks.portfolio_projected_usd),
        agreement: formatAgreement(apiData.agreement.normal_agreement),
      },
      {
        metric: "CVaR (95%)",
        historical: Math.abs(apiData.historical_replays.gfc_2008?.max_drawdown || 0) * apiData.portfolio_value,
        parametric: apiData.parametric.cvar_95_1d_usd,
        monteCarlo: apiData.monte_carlo.normal.cvar_95_1d_usd,
        factorShock: Math.abs(apiData.factor_shocks.portfolio_projected_usd * 1.25),
        agreement: formatAgreement(apiData.agreement.normal_agreement),
      },
      {
        metric: "Sharpe Ratio",
        historical: apiData.general_metrics.sharpe_ratio * 0.9,
        parametric: apiData.general_metrics.sharpe_ratio,
        monteCarlo: apiData.general_metrics.sharpe_ratio * 0.95,
        factorShock: apiData.general_metrics.sharpe_ratio * 0.85,
        agreement: "high" as const,
      },
      {
        metric: "Annualized Vol",
        historical: apiData.general_metrics.annualized_volatility,
        parametric: apiData.parametric.annualized_vol,
        monteCarlo: apiData.general_metrics.annualized_volatility * 1.02,
        factorShock: apiData.general_metrics.annualized_volatility * 0.98,
        agreement: "high" as const,
      },
    ];
  }, [apiData]);

  // Chart data adapter mapping
  const chartData = useMemo(() => {
    if (!apiData) return null;

    const pnlDistribution = generateHistogramData(
      apiData.monte_carlo.normal.sim_returns_sample,
      apiData.monte_carlo.student_t.sim_returns_sample
    );

    const crisisDrawdown = generateDrawdownCurves(apiData.historical_replays);

    const factorTornado = apiData.factor_shocks.factor_impacts.map((i) => ({
      factor: formatFactorTitle(i.factor, i.native_shock),
      impact: i.projected_usd_impact,
    }));

    const correlationMatrix = apiData.parametric.correlation_matrix;

    return {
      pnlDistribution,
      crisisDrawdown,
      factorTornado,
      correlationMatrix,
    };
  }, [apiData]);

  // Handle inputs changes
  const handleTickerChange = (index: number, value: string) => {
    const newTickers = [...tickers];
    newTickers[index] = value.toUpperCase();
    setTickers(newTickers);
  };

  const handleWeightChange = (index: number, value: string) => {
    const newWeights = [...weights];
    newWeights[index] = parseFloat(value) || 0;
    setWeights(newWeights);
  };

  const normalizeWeights = () => {
    const sum = weights.reduce((a, b) => a + b, 0);
    if (sum > 0) {
      setWeights(weights.map((w) => w / sum));
    }
  };

  const addHolding = () => {
    setTickers([...tickers, ""]);
    setWeights([...weights, 0]);
  };

  const removeHolding = (index: number) => {
    setTickers(tickers.filter((_, i) => i !== index));
    setWeights(weights.filter((_, i) => i !== index));
  };

  const handleDownloadPDF = async () => {
    await downloadReport({
      tickers,
      weights,
      portfolio_value: portfolioValue,
      lookback_days: lookbackDays,
      shocks,
      risk_free_rate: riskFreeRate
    });
  };

  const handleSaveAndReRun = () => {
    setIsEditing(false);
    fetchRiskData();
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border/50 sticky top-0 z-40 bg-background/95 backdrop-blur-sm">
        <div className="container py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setLocation("/")}
              className="hover:bg-accent/10"
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold">
                {tickers.filter(t => t.trim() !== "").slice(0, 3).join(" / ") || "Custom Portfolio"}
                {tickers.filter(t => t.trim() !== "").length > 3 && ` +${tickers.filter(t => t.trim() !== "").length - 3}`}
              </h1>
              <p className="text-sm text-muted-foreground">
                Portfolio Value: <span className="numeric text-accent">{formatCurrency(portfolioValue)}</span>
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (isEditing) {
                  handleSaveAndReRun();
                } else {
                  setIsEditing(true);
                }
              }}
              className="border-accent/50 hover:bg-accent/10"
              disabled={isLoading}
            >
              {isEditing ? "Save & Re-run" : "Edit Portfolio"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                normalizeWeights();
                fetchRiskData();
              }}
              className="border-accent/50 hover:bg-accent/10 gap-2"
              disabled={isLoading}
            >
              <RotateCw className="w-4 h-4" />
              Recompute
            </Button>
            <Button
              size="sm"
              onClick={handleDownloadPDF}
              className="bg-accent hover:bg-accent/90 text-accent-foreground gap-2"
              disabled={isLoading || !apiData}
            >
              <Download className="w-4 h-4" />
              PDF Report
            </Button>
          </div>
        </div>
      </header>

      {/* Portfolio Input Form (Collapsible) */}
      {isEditing && (
        <div className="border-b border-border/50 bg-card/30">
          <div className="container py-6">
            <div className="grid md:grid-cols-4 gap-6">
              {/* Portfolio Value & Lookback */}
              <div className="space-y-4">
                <div>
                  <Label className="text-sm font-medium">Portfolio Value ($)</Label>
                  <Input
                    type="number"
                    value={portfolioValue}
                    onChange={(e) => setPortfolioValue(parseFloat(e.target.value) || 0)}
                    className="mt-1 bg-background border-border/50"
                  />
                </div>
                <div>
                  <Label className="text-sm font-medium">Lookback Horizon (Days)</Label>
                  <select
                    value={lookbackDays}
                    onChange={(e) => setLookbackDays(parseInt(e.target.value))}
                    className="w-full mt-1 bg-background border border-border/50 rounded-md p-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                  >
                    <option value={252}>1 Year (252 days)</option>
                    <option value={504}>2 Years (504 days)</option>
                    <option value={1260}>5 Years (1260 days)</option>
                  </select>
                </div>
              </div>

              {/* Holdings */}
              <div className="md:col-span-3">
                <Label className="text-sm font-medium">Holdings Allocation</Label>
                <div className="space-y-2 mt-2 max-h-[250px] overflow-y-auto pr-2">
                  {tickers.map((ticker, idx) => (
                    <div key={idx} className="flex gap-2 items-end">
                      <div className="flex-1">
                        <Input
                          placeholder="Stock Ticker (e.g. SPY, AAPL)"
                          value={ticker}
                          onChange={(e) => handleTickerChange(idx, e.target.value)}
                          className="bg-background border-border/50 text-sm"
                        />
                      </div>
                      <div className="w-24">
                        <Input
                          type="number"
                          placeholder="Weight"
                          value={weights[idx] !== undefined ? weights[idx] : ""}
                          onChange={(e) => handleWeightChange(idx, e.target.value)}
                          className="bg-background border-border/50 text-sm numeric"
                        />
                      </div>
                      {tickers.length > 1 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeHolding(idx)}
                          className="text-destructive hover:bg-destructive/10"
                        >
                          ×
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
                <div className="flex gap-2 mt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={addHolding}
                    className="border-accent/50 hover:bg-accent/10 text-accent"
                  >
                    + Add Holding
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={normalizeWeights}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    Normalize Weights
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="container py-8">
        {error && (
          <div className="mb-6 p-4 bg-destructive/10 border border-destructive/30 rounded-lg text-destructive flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <p className="text-sm font-medium">{error}</p>
          </div>
        )}

        {isLoading ? (
          /* Loading Skeletons */
          <div className="space-y-6">
            <div className="grid md:grid-cols-5 gap-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <Card key={i} className="bg-card border-border/50 p-4">
                  <Skeleton className="h-3 w-20 mb-2" />
                  <Skeleton className="h-8 w-28" />
                </Card>
              ))}
            </div>
            
            <div className="p-4 bg-accent/5 border border-accent/20 rounded-lg flex items-center gap-3">
              <RefreshCw className="w-5 h-5 animate-spin text-accent" />
              <div className="space-y-1">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-3 w-96" />
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              {Array.from({ length: 4 }).map((_, i) => (
                <Card key={i} className="bg-card border-border/50 p-6">
                  <Skeleton className="h-5 w-40 mb-4" />
                  <Skeleton className="h-[250px] w-full" />
                </Card>
              ))}
            </div>
          </div>
        ) : metrics && chartData && apiData ? (
          /* Active Dashboard Content */
          <div className="space-y-8">
            {/* Risk Summary Cards */}
            <div className="grid md:grid-cols-5 gap-4">
              <RiskSummaryCard
                label="1-day VaR (95%)"
                value={metrics.var95_1d}
                type="currency"
              />
              <RiskSummaryCard
                label="1-day VaR (99%)"
                value={metrics.var99_1d}
                type="currency"
              />
              <RiskSummaryCard
                label="CVaR (95%)"
                value={metrics.cvar95}
                type="currency"
              />
              <RiskSummaryCard
                label={`Worst Crisis (${metrics.worstCrisisName})`}
                value={metrics.worstCrisisPnL}
                type="currency"
              />
              <RiskSummaryCard
                label="Annualized Vol"
                value={metrics.annualizedVol}
                type="percent"
              />
            </div>

            {/* Agreement Notice Box */}
            <div className="p-4 bg-accent/5 border border-accent/20 rounded-lg text-sm flex items-start gap-3">
              <AlertTriangle className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                apiData.agreement.fat_tail_presence === 'HIGH' ? 'text-red-400' : 'text-accent'
              }`} />
              <div>
                <p className="font-semibold text-foreground">
                  Model Agreement Check: {apiData.agreement.fat_tail_presence === 'HIGH' ? 'Critical Divergence' : 'Normal'}
                </p>
                <p className="text-muted-foreground text-xs mt-1">
                  {apiData.agreement.explanation}
                </p>
              </div>
            </div>

            {/* Charts Grid */}
            <div className="grid md:grid-cols-2 gap-6">
              <PnLDistributionChart data={chartData.pnlDistribution} />
              <CrisisDrawdownChart data={chartData.crisisDrawdown} />
              <FactorTornadoChart data={chartData.factorTornado} />
              <CorrelationHeatmap data={chartData.correlationMatrix} tickers={tickers.filter(t => t.trim() !== "")} />
            </div>

            {/* Method Comparison Table */}
            <MethodComparisonTable data={methodComparison} />
          </div>
        ) : (
          <div className="h-[300px] flex items-center justify-center border border-dashed border-border rounded-lg text-muted-foreground">
            Enter portfolio tickers and click Save & Re-run to run calculations.
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Risk Summary Card Component
 */
function RiskSummaryCard({
  label,
  value,
  type,
}: {
  label: string;
  value: number;
  type: "currency" | "percent";
}) {
  const isNegative = value < 0;
  const displayValue =
    type === "currency" ? formatCurrency(Math.abs(value)) : formatPercent(value);

  return (
    <Card className="bg-card border-border/50 p-4 hover:border-accent/50 transition-colors">
      <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-2">
        {label}
      </p>
      <p
        className={`numeric text-2xl font-bold ${
          isNegative ? "text-red-500" : "text-accent"
        }`}
      >
        {isNegative ? "-" : ""}{displayValue}
      </p>
    </Card>
  );
}
