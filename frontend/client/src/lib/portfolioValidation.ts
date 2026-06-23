/**
 * Portfolio Form Validation
 * Validates ticker symbols, weights, and portfolio constraints
 */

export interface ValidationError {
  field: string;
  index?: number;
  message: string;
  severity: "error" | "warning";
}

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
}

/**
 * Validate a single ticker symbol
 */
export function validateTicker(ticker: string, index: number): ValidationError[] {
  const errors: ValidationError[] = [];

  if (!ticker || ticker.trim() === "") {
    errors.push({
      field: "ticker",
      index,
      message: "Ticker symbol is required",
      severity: "error",
    });
    return errors;
  }

  const cleanTicker = ticker.trim().toUpperCase();
  if (!/^[A-Z]{1,5}$/.test(cleanTicker)) {
    errors.push({
      field: "ticker",
      index,
      message: "Ticker must be 1-5 letters (e.g., AAPL, MSFT)",
      severity: "error",
    });
  }

  return errors;
}

/**
 * Validate a single weight value
 */
export function validateWeight(weight: number, index: number): ValidationError[] {
  const errors: ValidationError[] = [];

  if (isNaN(weight) || weight === null || weight === undefined) {
    errors.push({
      field: "weight",
      index,
      message: "Weight must be a number",
      severity: "error",
    });
    return errors;
  }

  if (weight < 0) {
    errors.push({
      field: "weight",
      index,
      message: "Weight cannot be negative",
      severity: "error",
    });
  }

  if (weight === 0) {
    errors.push({
      field: "weight",
      index,
      message: "Weight must be greater than 0",
      severity: "error",
    });
  }

  if (weight > 1) {
    errors.push({
      field: "weight",
      index,
      message: "Weight cannot exceed 1.0 (100%)",
      severity: "error",
    });
  }

  return errors;
}

/**
 * Validate entire portfolio
 */
export function validatePortfolio(
  tickers: string[],
  weights: number[],
  portfolioValue: number
): ValidationResult {
  const errors: ValidationError[] = [];
  const warnings: ValidationError[] = [];

  // Check portfolio value
  if (!portfolioValue || portfolioValue <= 0) {
    errors.push({
      field: "portfolioValue",
      message: "Portfolio value must be greater than 0",
      severity: "error",
    });
  }

  // Check array lengths match
  if (tickers.length !== weights.length) {
    errors.push({
      field: "portfolio",
      message: "Number of tickers and weights must match",
      severity: "error",
    });
  }

  // Check minimum holdings
  if (tickers.length === 0) {
    errors.push({
      field: "portfolio",
      message: "Portfolio must have at least one holding",
      severity: "error",
    });
  }

  if (tickers.length > 20) {
    warnings.push({
      field: "portfolio",
      message: "Portfolio has more than 20 holdings (may reduce performance)",
      severity: "warning",
    });
  }

  // Validate each ticker and weight
  const tickerErrors: ValidationError[] = [];
  const weightErrors: ValidationError[] = [];

  tickers.forEach((ticker, idx) => {
    tickerErrors.push(...validateTicker(ticker, idx));
  });

  weights.forEach((weight, idx) => {
    weightErrors.push(...validateWeight(weight, idx));
  });

  errors.push(...tickerErrors);
  errors.push(...weightErrors);

  // Check for duplicate tickers
  const uniqueTickers = new Set(tickers.map((t) => t.toUpperCase()));
  if (uniqueTickers.size < tickers.length) {
    errors.push({
      field: "portfolio",
      message: "Portfolio contains duplicate ticker symbols",
      severity: "error",
    });
  }

  // Check weight sum (allow small floating point error)
  const weightSum = weights.reduce((a, b) => a + b, 0);
  const tolerance = 0.01; // 1% tolerance

  if (Math.abs(weightSum - 1.0) > tolerance) {
    if (weightSum === 0) {
      errors.push({
        field: "portfolio",
        message: "Portfolio weights sum to 0. All weights must be positive.",
        severity: "error",
      });
    } else {
      warnings.push({
        field: "portfolio",
        message: `Portfolio weights sum to ${(weightSum * 100).toFixed(1)}%. Auto-normalize on compute.`,
        severity: "warning",
      });
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  };
}

/**
 * Get user-friendly error message for a field
 */
export function getFieldError(
  errors: ValidationError[],
  field: string,
  index?: number
): string | null {
  const error = errors.find(
    (e) => e.field === field && (index === undefined || e.index === index)
  );
  return error ? error.message : null;
}

/**
 * Check if a field has any errors
 */
export function hasFieldError(
  errors: ValidationError[],
  field: string,
  index?: number
): boolean {
  return errors.some(
    (e) => e.field === field && (index === undefined || e.index === index)
  );
}
