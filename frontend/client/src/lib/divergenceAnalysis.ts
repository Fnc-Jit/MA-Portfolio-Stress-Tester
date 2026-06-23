/**
 * Model Divergence Analysis
 * Computes agreement levels between risk models based on output variance
 */

export interface DivergenceAnalysis {
  metric: string;
  values: {
    historical: number;
    parametric: number;
    monteCarlo: number;
    factorShock: number;
  };
  mean: number;
  stdDev: number;
  coefficientOfVariation: number;
  agreement: "high" | "medium" | "low";
  divergencePercent: number;
}

/**
 * Compute coefficient of variation (CV) to assess model agreement
 * CV = (std dev / mean) * 100
 * 
 * Interpretation:
 * - CV < 5%: High agreement (models closely aligned)
 * - 5% <= CV < 15%: Medium agreement (some divergence)
 * - CV >= 15%: Low agreement (significant divergence)
 */
export function analyzeModelDivergence(
  historical: number,
  parametric: number,
  monteCarlo: number,
  factorShock: number
): DivergenceAnalysis["agreement"] {
  const values = [historical, parametric, monteCarlo, factorShock];
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  
  if (mean === 0) return "high";
  
  const variance =
    values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
  const stdDev = Math.sqrt(variance);
  const cv = (stdDev / Math.abs(mean)) * 100;

  if (cv < 5) return "high";
  if (cv < 15) return "medium";
  return "low";
}

/**
 * Full divergence analysis for a metric across all models
 */
export function computeDivergenceAnalysis(
  metric: string,
  historical: number,
  parametric: number,
  monteCarlo: number,
  factorShock: number
): DivergenceAnalysis {
  const values = {
    historical,
    parametric,
    monteCarlo,
    factorShock,
  };

  const numValues = Object.values(values).length;
  const mean =
    Object.values(values).reduce((a, b) => a + b, 0) / numValues;

  if (mean === 0) {
    return {
      metric,
      values,
      mean,
      stdDev: 0,
      coefficientOfVariation: 0,
      agreement: "high",
      divergencePercent: 0,
    };
  }

  const variance =
    Object.values(values).reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) /
    numValues;
  const stdDev = Math.sqrt(variance);
  const cv = (stdDev / Math.abs(mean)) * 100;

  // Determine agreement level
  let agreement: "high" | "medium" | "low";
  if (cv < 5) agreement = "high";
  else if (cv < 15) agreement = "medium";
  else agreement = "low";

  // Calculate max divergence from mean as percentage
  const maxDeviation = Math.max(
    ...Object.values(values).map((v) => Math.abs(v - mean))
  );
  const divergencePercent = (maxDeviation / Math.abs(mean)) * 100;

  return {
    metric,
    values,
    mean,
    stdDev,
    coefficientOfVariation: cv,
    agreement,
    divergencePercent,
  };
}

/**
 * Generate insights about model divergence
 */
export function getDivergenceInsight(analysis: DivergenceAnalysis): string {
  if (analysis.agreement === "high") {
    return "All models closely aligned. High confidence in estimate.";
  } else if (analysis.agreement === "medium") {
    return `Models show some divergence (${analysis.divergencePercent.toFixed(1)}%). Consider fat-tail adjustments.`;
  } else {
    return `Significant divergence detected (${analysis.divergencePercent.toFixed(1)}%). Non-normal returns likely. Use Monte Carlo with Student-t.`;
  }
}
