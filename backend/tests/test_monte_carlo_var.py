import pytest
import numpy as np
import pandas as pd
from risk_engine.monte_carlo_var import (
    is_positive_definite, 
    make_positive_definite, 
    run_monte_carlo_simulation
)
from risk_engine.parametric_var import calculate_parametric_var

def test_covariance_matrix_pd_adjustment():
    """
    Test positive definite checker and adjustment functions.
    """
    # 1. A symmetric matrix with negative eigenvalues (non-PD)
    # E.g. [[1.0, 2.0], [2.0, 1.0]]
    # det = 1 - 4 = -3
    matrix_non_pd = np.array([[1.0, 2.0], [2.0, 1.0]])
    
    assert not is_positive_definite(matrix_non_pd)
    
    # 2. Adjust the matrix to make it PD
    matrix_pd = make_positive_definite(matrix_non_pd, epsilon=0.01)
    
    assert is_positive_definite(matrix_pd)
    # Verify diagonal elements are larger
    assert matrix_pd[0, 0] > 1.0
    assert matrix_pd[1, 1] > 1.0

def test_monte_carlo_simulation_convergence():
    """
    Verifies that Monte Carlo normal simulated VaR converges to parametric analytical VaR
    for a simple asset portfolio.
    """
    np.random.seed(123)
    n_days = 200
    dates = pd.date_range(start="2023-01-01", periods=n_days)
    
    # Generate daily returns
    r_A = np.random.normal(0.0005, 0.012, n_days)
    r_B = np.random.normal(0.0008, 0.018, n_days)
    
    p_A = 100 * np.exp(np.cumsum(r_A))
    p_B = 100 * np.exp(np.cumsum(r_B))
    
    df_prices = pd.DataFrame({
        "A": p_A,
        "B": p_B
    }, index=dates)
    
    weights = [0.4, 0.6]
    portfolio_value = 5_000_000.0
    
    # Compute Parametric
    param_res = calculate_parametric_var(df_prices, weights, portfolio_value, lookback_days=n_days)
    
    # Compute Monte Carlo (high sims for better convergence check)
    mc_res = run_monte_carlo_simulation(
        df_prices, 
        weights, 
        portfolio_value=portfolio_value, 
        lookback_days=n_days, 
        n_sims=15000
    )
    
    # Parametric VaR 95% 1-day
    p_var_95 = param_res["var_95_1d_pct"]
    # Monte Carlo Normal VaR 95% 1-day
    mc_var_95 = mc_res["normal"]["var_95_1d_pct"]
    
    # They should be within 5% of each other
    pct_diff = abs(p_var_95 - mc_var_95) / p_var_95
    assert pct_diff < 0.05, f"Monte Carlo and Parametric VaR diverge by {pct_diff:.2%}"
    
    # Verify that Student-t VaR is larger than normal VaR (fat tails)
    mc_t_var_95 = mc_res["student_t"]["var_95_1d_pct"]
    assert mc_t_var_95 >= mc_var_95 * 0.95  # Student-t should be comparable or larger
