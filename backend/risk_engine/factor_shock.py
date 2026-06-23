import numpy as np
import pandas as pd
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def run_factor_shock_analysis(
    prices: pd.DataFrame,
    macro_factors: pd.DataFrame,
    weights: list[float],
    shocks: Dict[str, float],  # Native units, e.g. {"vix": 0.50, "y10": 0.02, "oil": -0.20, "usd": 0.05}
    portfolio_value: float = 10_000_000.0,
    lookback_days: int = 504
) -> Dict[str, Any]:
    """
    Regresses portfolio asset returns on standardized macro factors.
    Projects the portfolio dollar and percentage impact under a user-defined shock vector.
    
    Macro factor definitions for changes:
    - VIX: Daily percentage change (e.g. VIX increases from 20 to 30 is a +50% shock = 0.50)
    - 10Y Yield: Daily level difference in percentage points (e.g. +200 bps = +2.0% yield change = 2.0)
    - Oil: Daily percentage change
    - USD: Daily percentage change
    """
    if len(weights) != prices.shape[1]:
        raise ValueError("Weights size must match number of assets.")
    if not np.isclose(sum(weights), 1.0):
        raise ValueError("Weights must sum to 1.0.")
        
    weights_arr = np.array(weights)
    
    # 1. Align data and calculate changes/returns
    df_prices_lookback = prices.tail(lookback_days)
    asset_returns = df_prices_lookback.pct_change().dropna()
    
    # Calculate macro changes
    macro_changes = pd.DataFrame(index=macro_factors.index)
    
    # VIX: percentage change
    macro_changes["vix"] = macro_factors["vix"].pct_change()
    # 10Y Yield: daily difference (in percentage points)
    # E.g. if yield goes from 3.5 to 3.7, change is +0.2
    macro_changes["y10"] = macro_factors["y10"].diff()
    # Oil: percentage change
    macro_changes["oil"] = macro_factors["oil"].pct_change()
    # USD: percentage change
    macro_changes["usd"] = macro_factors["usd"].pct_change()
    
    # Align dates
    combined = asset_returns.join(macro_changes, how="inner").dropna()
    if len(combined) < 10:
        raise ValueError(f"Too few overlapping observations ({len(combined)}) between assets and macro factors.")
        
    tickers = list(prices.columns)
    factor_names = ["vix", "y10", "oil", "usd"]
    
    # Extract aligned returns and factors
    aligned_returns = combined[tickers]
    aligned_factors = combined[factor_names]
    
    # 2. Standardize factors (z-score) to make betas comparable
    # Record mean and std of native changes to convert native shocks to standardized shocks later
    factor_means = aligned_factors.mean()
    factor_stds = aligned_factors.std()
    
    # Avoid division by zero
    factor_stds = factor_stds.replace(0, 1e-8)
    
    factors_standardized = (aligned_factors - factor_means) / factor_stds
    
    # Prepare regression matrix X (shape T x 5, including intercept)
    T = len(combined)
    X = np.column_stack([np.ones(T), factors_standardized.values])
    
    # 3. Fit OLS regression for each asset
    # betas dict stores factor betas per ticker
    asset_betas = {}  # ticker -> [intercept, beta_vix, beta_y10, beta_oil, beta_usd]
    
    for ticker in tickers:
        Y = aligned_returns[ticker].values
        # Solve least squares: X beta = Y
        beta_coefficients, _, _, _ = np.linalg.lstsq(X, Y, rcond=None)
        asset_betas[ticker] = beta_coefficients
        
    # 4. Compute portfolio-level betas (weighted sum of asset betas)
    # beta_coefficients is a vector [intercept, beta_vix, beta_y10, beta_oil, beta_usd]
    portfolio_betas = np.zeros(5)
    for i, ticker in enumerate(tickers):
        portfolio_betas += weights_arr[i] * asset_betas[ticker]
        
    # 5. Process the user shock vector
    # Default values if keys are missing from shocks input
    native_shocks = {f: shocks.get(f, 0.0) for f in factor_names}
    
    # Standardize shocks: Shock_std = Shock_native / std_native_changes
    std_shocks = {}
    for f in factor_names:
        std_shocks[f] = native_shocks[f] / factor_stds[f]
        
    # 6. Project impact
    # Expected return = \sum_f beta_portfolio_f * Shock_std_f
    projected_returns_per_asset = {}
    projected_usd_per_asset = {}
    
    for ticker in tickers:
        betas = asset_betas[ticker]  # [intercept, beta_vix, beta_y10, beta_oil, beta_usd]
        # Intercept is daily expected return. Usually we do not compound intercept during stress shock,
        # but just project the direct beta impact: \sum beta_f * Shock_std_f
        impact = 0.0
        for idx, f in enumerate(factor_names):
            impact += betas[idx + 1] * std_shocks[f]
        projected_returns_per_asset[ticker] = float(impact)
        
    # Portfolio projected return is weighted sum of asset projected returns
    portfolio_projected_return = float(sum(weights[i] * projected_returns_per_asset[tickers[i]] for i in range(len(tickers))))
    portfolio_projected_usd = portfolio_projected_return * portfolio_value
    
    # Asset projected USD impacts
    for i, ticker in enumerate(tickers):
        asset_val = weights[i] * portfolio_value
        projected_usd_per_asset[ticker] = projected_returns_per_asset[ticker] * asset_val
        
    # Format asset beta details for response
    asset_beta_details = []
    for ticker in tickers:
        betas = asset_betas[ticker]
        asset_beta_details.append({
            "ticker": ticker,
            "betas": {
                "vix": float(betas[1]),
                "y10": float(betas[2]),
                "oil": float(betas[3]),
                "usd": float(betas[4])
            },
            "projected_return": projected_returns_per_asset[ticker],
            "projected_usd": projected_usd_per_asset[ticker]
        })
        
    # Detail factor level impacts for tornado chart
    factor_impacts = []
    for idx, f in enumerate(factor_names):
        factor_beta_port = portfolio_betas[idx + 1]
        factor_impact_pct = factor_beta_port * std_shocks[f]
        factor_impacts.append({
            "factor": f,
            "beta": float(factor_beta_port),
            "native_shock": native_shocks[f],
            "std_shock": std_shocks[f],
            "projected_return_impact": float(factor_impact_pct),
            "projected_usd_impact": float(factor_impact_pct * portfolio_value)
        })
        
    return {
        "portfolio_projected_return": portfolio_projected_return,
        "portfolio_projected_usd": portfolio_projected_usd,
        "portfolio_betas": {
            "vix": float(portfolio_betas[1]),
            "y10": float(portfolio_betas[2]),
            "oil": float(portfolio_betas[3]),
            "usd": float(portfolio_betas[4])
        },
        "factor_impacts": factor_impacts,
        "asset_details": asset_beta_details,
        "shocks_applied": native_shocks
    }
