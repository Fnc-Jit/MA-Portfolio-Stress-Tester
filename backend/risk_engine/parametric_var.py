import numpy as np
import pandas as pd
import scipy.stats as stats
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def calculate_parametric_var(
    prices: pd.DataFrame, 
    weights: list[float], 
    portfolio_value: float = 10_000_000.0,
    lookback_days: int = 504
) -> Dict[str, Any]:
    """
    Calculates Parametric Value at Risk (VaR) and Conditional Value at Risk (CVaR)
    for a portfolio given price history and weights.
    
    Parameters:
    - prices: DataFrame of adjusted close prices (Date index, tickers as columns)
    - weights: list of float weights (must sum to 1.0)
    - portfolio_value: total USD portfolio value
    - lookback_days: lookback window in trading days (default 2 years = 504 days)
    """
    # 1. Validation
    if len(weights) != prices.shape[1]:
        raise ValueError("Weights list size must match number of ticker columns.")
    if not np.isclose(sum(weights), 1.0):
        raise ValueError("Weights must sum to 1.0 (or close to it).")
        
    weights_arr = np.array(weights)
    
    # Slice prices for lookback period
    df_lookback = prices.tail(lookback_days)
    if len(df_lookback) < 10:
        raise ValueError(f"Too few historical dates ({len(df_lookback)}) for risk parameters calculation.")
        
    # 2. Calculate daily returns (we use simple returns for portfolio calculations as standard practice,
    # but for covariance and vol log returns can be used. Let's calculate simple daily returns here)
    returns = df_lookback.pct_change().dropna()
    
    # 3. Calculate mean returns and covariance matrix
    # Mean vector mu (daily)
    mu = returns.mean().values
    # Covariance matrix Sigma (daily)
    Sigma = returns.cov().values
    # Correlation matrix for reports
    Correlation = returns.corr().values
    
    # 4. Portfolio Volatility and Expected Return
    # Portfolio expected return: w^T mu
    port_expected_return_daily = float(np.dot(weights_arr, mu))
    # Portfolio variance: w^T Sigma w
    port_variance_daily = float(weights_arr.T @ Sigma @ weights_arr)
    # Portfolio standard deviation (volatility)
    port_vol_daily = np.sqrt(port_variance_daily)
    
    # Annualized metrics (assuming 252 trading days per year)
    port_vol_annualized = port_vol_daily * np.sqrt(252)
    port_expected_return_annualized = port_expected_return_daily * 252
    
    # 5. Parametric VaR and CVaR calculations using the standard normal distribution
    # Z-scores
    z_95 = stats.norm.ppf(0.95)  # 1.64485
    z_99 = stats.norm.ppf(0.99)  # 2.32635
    
    # Value at Risk (1-day, expressed as positive dollar losses, and percent losses)
    # Using the zero-mean formula requested: VaR = z * sigma * portfolio_value
    var_95_1d_pct = z_95 * port_vol_daily
    var_99_1d_pct = z_99 * port_vol_daily
    
    var_95_1d_usd = var_95_1d_pct * portfolio_value
    var_99_1d_usd = var_99_1d_pct * portfolio_value
    
    # 10-day VaR using square root of time rule
    var_95_10d_pct = var_95_1d_pct * np.sqrt(10)
    var_99_10d_pct = var_99_1d_pct * np.sqrt(10)
    var_95_10d_usd = var_95_1d_usd * np.sqrt(10)
    var_99_10d_usd = var_99_1d_usd * np.sqrt(10)
    
    # Conditional VaR (Expected Shortfall) using normal distribution formula:
    # CVaR = sigma * (pdf(z) / (1 - alpha)) * portfolio_value
    pdf_z_95 = stats.norm.pdf(z_95)
    pdf_z_99 = stats.norm.pdf(z_99)
    
    cvar_95_1d_pct = port_vol_daily * (pdf_z_95 / 0.05)
    cvar_99_1d_pct = port_vol_daily * (pdf_z_99 / 0.01)
    
    cvar_95_1d_usd = cvar_95_1d_pct * portfolio_value
    cvar_99_1d_usd = cvar_99_1d_pct * portfolio_value
    
    # 10-day CVaR using square root of time
    cvar_95_10d_pct = cvar_95_1d_pct * np.sqrt(10)
    cvar_99_10d_pct = cvar_99_1d_pct * np.sqrt(10)
    cvar_95_10d_usd = cvar_95_1d_usd * np.sqrt(10)
    cvar_99_10d_usd = cvar_99_1d_usd * np.sqrt(10)
    
    # Prepare ticker specific volatilities and correlation lists
    asset_vols_daily = np.sqrt(np.diag(Sigma))
    asset_vols_annualized = asset_vols_daily * np.sqrt(252)
    
    tickers = list(prices.columns)
    asset_metrics = []
    for i, ticker in enumerate(tickers):
        asset_metrics.append({
            "ticker": ticker,
            "weight": float(weights[i]),
            "daily_vol": float(asset_vols_daily[i]),
            "annualized_vol": float(asset_vols_annualized[i]),
            "expected_return_annualized": float(mu[i] * 252)
        })
        
    return {
        "portfolio_value": portfolio_value,
        "daily_vol": float(port_vol_daily),
        "annualized_vol": float(port_vol_annualized),
        "expected_return_daily": float(port_expected_return_daily),
        "expected_return_annualized": float(port_expected_return_annualized),
        "var_95_1d_pct": float(var_95_1d_pct),
        "var_99_1d_pct": float(var_99_1d_pct),
        "var_95_1d_usd": float(var_95_1d_usd),
        "var_99_1d_usd": float(var_99_1d_usd),
        "var_95_10d_pct": float(var_95_10d_pct),
        "var_99_10d_pct": float(var_99_10d_pct),
        "var_95_10d_usd": float(var_95_10d_usd),
        "var_99_10d_usd": float(var_99_10d_usd),
        "cvar_95_1d_pct": float(cvar_95_1d_pct),
        "cvar_99_1d_pct": float(cvar_99_1d_pct),
        "cvar_95_1d_usd": float(cvar_95_1d_usd),
        "cvar_99_1d_usd": float(cvar_99_1d_usd),
        "cvar_95_10d_pct": float(cvar_95_10d_pct),
        "cvar_99_10d_pct": float(cvar_99_10d_pct),
        "cvar_95_10d_usd": float(cvar_95_10d_usd),
        "cvar_99_10d_usd": float(cvar_99_10d_usd),
        "asset_metrics": asset_metrics,
        "correlation_matrix": Correlation.tolist(),
        "tickers": tickers
    }
