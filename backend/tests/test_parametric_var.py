import pytest
import numpy as np
import pandas as pd
from risk_engine.parametric_var import calculate_parametric_var

def test_parametric_var_math():
    """
    Test Parametric VaR calculation correctness on a synthetic 2-asset portfolio
    with zero correlation and known volatilities.
    """
    np.random.seed(42)
    n_days = 100
    dates = pd.date_range(start="2023-01-01", periods=n_days)
    
    # Generate daily returns:
    # Asset A: constant volatility of 1% (daily)
    # Asset B: constant volatility of 2% (daily)
    # Mean returns = 0.0
    r_A = np.random.normal(0, 0.01, n_days)
    r_B = np.random.normal(0, 0.02, n_days)
    
    # Convert returns to price paths starting at 100
    p_A = 100 * np.exp(np.cumsum(r_A))
    p_B = 100 * np.exp(np.cumsum(r_B))
    
    df_prices = pd.DataFrame({
        "ASSET_A": p_A,
        "ASSET_B": p_B
    }, index=dates)
    
    # Equal weighting
    weights = [0.5, 0.5]
    portfolio_value = 10_000_000.0
    
    # Calculate daily volatilities of assets from our returns to check expected portfolio vol
    # Expected port vol = sqrt( w_A^2 * vol_A^2 + w_B^2 * vol_B^2 + 2 * w_A * w_B * cov_AB )
    returns_df = df_prices.pct_change().dropna()
    cov_matrix = returns_df.cov().values
    
    w = np.array(weights)
    expected_variance = w.T @ cov_matrix @ w
    expected_vol = np.sqrt(expected_variance)
    
    # Run calculation
    results = calculate_parametric_var(
        df_prices, 
        weights, 
        portfolio_value=portfolio_value, 
        lookback_days=100
    )
    
    # Assertions
    assert np.isclose(results["daily_vol"], expected_vol)
    assert np.isclose(results["annualized_vol"], expected_vol * np.sqrt(252))
    
    # Check VaR value: VaR = z_alpha * vol_portfolio * portfolio_value
    z_95 = 1.6448536269514722  # scipy.stats.norm.ppf(0.95)
    expected_var_95_pct = z_95 * expected_vol
    expected_var_95_usd = expected_var_95_pct * portfolio_value
    
    assert np.isclose(results["var_95_1d_pct"], expected_var_95_pct)
    assert np.isclose(results["var_95_1d_usd"], expected_var_95_usd)
    
    # Check 10-day VaR
    assert np.isclose(results["var_95_10d_pct"], expected_var_95_pct * np.sqrt(10))
    assert np.isclose(results["var_95_10d_usd"], expected_var_95_usd * np.sqrt(10))
    
    # Check that CVaR > VaR
    assert results["cvar_95_1d_pct"] > results["var_95_1d_pct"]
    assert results["cvar_99_1d_pct"] > results["var_99_1d_pct"]
