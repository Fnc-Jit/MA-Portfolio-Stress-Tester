/**
 * API client to connect the React frontend with the FastAPI Python backend
 */

export interface RiskRequest {
  tickers: string[];
  weights: number[];
  portfolio_value: number;
  lookback_days: number;
  shocks: Record<string, number>;
  risk_free_rate: number;
}

export interface ReplayPathPoint {
  date: string;
  value: number;
}

export interface HistoricalReplayResult {
  crisis_name: string;
  start_date: string;
  end_date: string;
  max_drawdown: number;
  worst_day: number;
  worst_day_date: string;
  final_return: number;
  returns_path: ReplayPathPoint[];
  error?: string;
}

export interface FactorImpact {
  factor: string;
  beta: number;
  native_shock: number;
  std_shock: number;
  projected_return_impact: number;
  projected_usd_impact: number;
}

export interface AssetMetrics {
  ticker: string;
  weight: number;
  daily_vol: number;
  annualized_vol: number;
  expected_return_annualized: number;
}

export interface RiskComputeResponse {
  portfolio_value: number;
  lookback_days: number;
  general_metrics: {
    annualized_volatility: number;
    annualized_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
  };
  parametric: {
    portfolio_value: number;
    daily_vol: number;
    annualized_vol: number;
    expected_return_daily: number;
    expected_return_annualized: number;
    var_95_1d_pct: number;
    var_99_1d_pct: number;
    var_95_1d_usd: number;
    var_99_1d_usd: number;
    cvar_95_1d_pct: number;
    cvar_99_1d_pct: number;
    cvar_95_1d_usd: number;
    cvar_99_1d_usd: number;
    asset_metrics: AssetMetrics[];
    correlation_matrix: number[][];
    tickers: string[];
  };
  monte_carlo: {
    normal: {
      var_95_1d_pct: number;
      var_99_1d_pct: number;
      var_95_1d_usd: number;
      var_99_1d_usd: number;
      cvar_95_1d_pct: number;
      cvar_99_1d_pct: number;
      cvar_95_1d_usd: number;
      cvar_99_1d_usd: number;
      sim_returns_sample: number[];
    };
    student_t: {
      var_95_1d_pct: number;
      var_99_1d_pct: number;
      var_95_1d_usd: number;
      var_99_1d_usd: number;
      cvar_95_1d_pct: number;
      cvar_99_1d_pct: number;
      cvar_95_1d_usd: number;
      cvar_99_1d_usd: number;
      sim_returns_sample: number[];
    };
  };
  historical_replays: Record<string, HistoricalReplayResult>;
  factor_shocks: {
    portfolio_projected_return: number;
    portfolio_projected_usd: number;
    portfolio_betas: Record<string, number>;
    factor_impacts: FactorImpact[];
  };
  agreement: {
    diff_mc_normal: number;
    diff_mc_student_t: number;
    normal_agreement: string;
    fat_tail_presence: string;
    explanation: string;
  };
}

/**
 * Resolves the Backend API URL based on environment variables or local fallback.
 */
export function getApiUrl(): string {
  // Use VITE_API_URL if configured, otherwise default to local FastAPI dev server
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl) return envUrl.replace(/\/$/, "");
  
  if (typeof window !== "undefined") {
    // If running in production (built) and VITE_API_URL is unset, default to the host URL
    if (import.meta.env.PROD) {
      return window.location.origin;
    }
  }
  return "http://localhost:8000";
}

/**
 * Calls `/portfolio/validate` to verify if tickers exist on Yahoo Finance
 */
export async function validateTickers(tickers: string[], weights: number[]): Promise<{ isValid: boolean; message: string }> {
  const url = `${getApiUrl()}/portfolio/validate`;
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tickers, weights }),
    });

    const data = await response.json();
    if (!response.ok) {
      return {
        isValid: false,
        message: data.detail?.message || "Invalid ticker symbols detected.",
      };
    }
    return { isValid: true, message: "Valid portfolio tickers." };
  } catch (error) {
    console.error("API connection error in validateTickers:", error);
    return {
      isValid: false,
      message: "Could not connect to the validation server. Running calculations directly.",
    };
  }
}

/**
 * Computes portfolio risk parameters on the FastAPI backend
 */
export async function computeRiskMetrics(payload: RiskRequest): Promise<RiskComputeResponse> {
  const url = `${getApiUrl()}/risk/compute`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Risk engine failed to compute portfolio statistics.");
  }

  return response.json();
}

/**
 * Requests the backend to generate a PDF/HTML risk report and triggers browser file download.
 */
export async function downloadReport(payload: RiskRequest): Promise<void> {
  const url = `${getApiUrl()}/risk/report`;
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error("Failed to download PDF report from the API.");
    }

    const blob = await response.blob();
    const contentType = response.headers.get("content-type") || "application/pdf";
    const isPdf = contentType.includes("pdf");
    const filename = isPdf ? "portfolio_risk_report.pdf" : "portfolio_risk_report.html";

    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  } catch (error) {
    console.error("Error downloading report:", error);
    alert("Error downloading report. Please ensure the backend is running.");
  }
}

/**
 * Bins raw simulation sample returns into histogram data for charting.
 */
export function generateHistogramData(
  normalReturns: number[],
  studentTReturns: number[],
  numBins = 15
): Array<{ range: string; normal: number; student_t: number }> {
  if (!normalReturns.length || !studentTReturns.length) return [];

  // Find min and max boundaries across both lists
  const allReturns = [...normalReturns, ...studentTReturns];
  const min = Math.min(...allReturns);
  const max = Math.max(...allReturns);
  const binWidth = (max - min) / numBins;

  // Initialize bins
  const bins = Array.from({ length: numBins }, (_, i) => {
    const binStart = min + i * binWidth;
    const binEnd = binStart + binWidth;
    const rangeName = `${(binStart * 100).toFixed(1)}% to ${(binEnd * 100).toFixed(1)}%`;
    return {
      range: rangeName,
      normal: 0,
      student_t: 0,
      start: binStart,
      end: binEnd,
    };
  });

  // Sort returns into bins
  normalReturns.forEach((r) => {
    let index = Math.floor((r - min) / binWidth);
    if (index >= numBins) index = numBins - 1;
    if (index >= 0) bins[index].normal += 1;
  });

  studentTReturns.forEach((r) => {
    let index = Math.floor((r - min) / binWidth);
    if (index >= numBins) index = numBins - 1;
    if (index >= 0) bins[index].student_t += 1;
  });

  // Remove local helper ranges and return
  return bins.map(({ range, normal, student_t }) => ({ range, normal, student_t }));
}

/**
 * Aligns historical replay datasets into relative Day 0 -> Day N curves.
 */
export function generateDrawdownCurves(
  replays: Record<string, HistoricalReplayResult>
): Array<{
  date: number;
  gfc2008: number;
  covid2020: number;
  taper2013: number;
  hike2022: number;
}> {
  const alignPoints: Array<{ gfc2008: number; covid2020: number; taper2013: number; hike2022: number }> = [];

  const gfc = replays.gfc_2008?.returns_path || [];
  const covid = replays.covid_2020?.returns_path || [];
  const taper = replays.taper_2013?.returns_path || [];
  const hike = replays.hike_2022?.returns_path || [];

  // Find max days
  const maxDays = Math.max(gfc.length, covid.length, taper.length, hike.length);

  for (let day = 0; day < maxDays; day++) {
    alignPoints.push({
      gfc2008: gfc[day] !== undefined ? gfc[day].value : (gfc[gfc.length - 1]?.value || 0),
      covid2020: covid[day] !== undefined ? covid[day].value : (covid[covid.length - 1]?.value || 0),
      taper2013: taper[day] !== undefined ? taper[day].value : (taper[taper.length - 1]?.value || 0),
      hike2022: hike[day] !== undefined ? hike[day].value : (hike[hike.length - 1]?.value || 0),
    });
  }

  return alignPoints.map((pt, idx) => ({ date: idx, ...pt }));
}

/**
 * Format currency for display
 */
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Format percentage for display
 */
export function formatPercent(value: number, decimals = 2): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * User-friendly formatting of factors
 */
export function formatFactorTitle(factor: string, shockVal: number): string {
  const map: Record<string, string> = {
    vix: "VIX Volatility Index",
    y10: "10Y Treasury Yield",
    oil: "Crude Oil (WTI)",
    usd: "US Dollar Index",
  };
  const title = map[factor] || factor.toUpperCase();
  const shockStr = factor === "y10" ? `${(shockVal * 100).toFixed(0)} bps` : `${(shockVal * 100).toFixed(0)}%`;
  return `${title} (${shockVal >= 0 ? "+" : ""}${shockStr})`;
}
