import numpy as np
import pandas as pd
import scipy.linalg as linalg
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

def is_positive_definite(matrix: np.ndarray) -> bool:
    """Check if matrix is positive definite by trying Cholesky factorization."""
    try:
        linalg.cholesky(matrix, lower=True)
        return True
    except linalg.LinAlgError:
        return False

def make_positive_definite(matrix: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
    """
    Applies a ridge adjustment (adds small epsilon to the diagonal)
    to force the covariance matrix to be positive definite.
    """
    adjusted = matrix.copy()
    n = adjusted.shape[0]
    # Add increasing diagonal noise until it is positive definite
    for i in range(10):
        if is_positive_definite(adjusted):
            if i > 0:
                logger.info(f"Covariance matrix made positive definite after {i} ridge adjustments.")
            return adjusted
        # Add epsilon to diagonal
        np.fill_diagonal(adjusted, np.diagonal(adjusted) + epsilon * (10 ** i))
        
    # If Cholesky still fails, perform spectral reconstruction (zero out negative eigenvalues)
    logger.warning("Cholesky failed after diagonal additions. Performing spectral reconstruction.")
    eigvals, eigvecs = linalg.eigh(matrix)
    # Clamp eigenvalues to be positive
    eigvals = np.maximum(eigvals, epsilon)
    # Reconstruct matrix
    reconstructed = eigvecs @ np.diag(eigvals) @ eigvecs.T
    return (reconstructed + reconstructed.T) / 2.0

def run_monte_carlo_simulation(
    prices: pd.DataFrame,
    weights: list[float],
    portfolio_value: float = 10_000_000.0,
    lookback_days: int = 504,
    n_sims: int = 10000,
    student_t_df: int = 5
) -> Dict[str, Any]:
    """
    Runs Monte Carlo simulation for portfolio Value at Risk and Conditional Value at Risk
    using both normal and Student-t (fat-tailed) distributions.
    """
    if len(weights) != prices.shape[1]:
        raise ValueError("Weights size must match number of assets.")
    if not np.isclose(sum(weights), 1.0):
        raise ValueError("Weights must sum to 1.0.")
        
    weights_arr = np.array(weights)
    
    # Slice prices for lookback period
    df_lookback = prices.tail(lookback_days)
    returns = df_lookback.pct_change().dropna()
    
    # Calculate daily mean returns and covariance matrix
    mu = returns.mean().values
    Sigma = returns.cov().values
    
    # Ensure Sigma is positive definite for Cholesky decomposition
    Sigma_pd = make_positive_definite(Sigma)
    
    # Cholesky decomposition L (lower triangular)
    # Sigma = L L^T
    L = linalg.cholesky(Sigma_pd, lower=True)
    
    n_assets = len(weights)
    np.random.seed(42)  # For reproducibility
    
    # --- 1. Normal Distribution Simulation ---
    # Draw independent standard normals: shape (n_assets, n_sims)
    z_normal = np.random.standard_normal((n_assets, n_sims))
    # Correlated returns: mu + L @ z_normal
    sim_returns_normal = mu[:, np.newaxis] + L @ z_normal
    # Portfolio returns: shape (n_sims,)
    port_returns_normal = sim_returns_normal.T @ weights_arr
    
    # --- 2. Student-t Distribution Simulation (df = student_t_df) ---
    # Draw standard normals
    z_t_norm = np.random.standard_normal((n_assets, n_sims))
    # Draw Chi-square random variables for scaling
    # Variance of standard Student-t is df / (df - 2).
    # To maintain the target covariance matrix Sigma exactly, we scale the Student-t draws by sqrt((df-2)/df).
    # Let V be Chi-square(df), then T = Z * sqrt(df / V).
    # T_adjusted = T * sqrt((df-2)/df) = Z * sqrt((df-2)/V).
    chi_square = np.random.chisquare(student_t_df, size=(1, n_sims))
    scale_factor = np.sqrt((student_t_df - 2.0) / chi_square)
    z_t = z_t_norm * scale_factor
    
    sim_returns_t = mu[:, np.newaxis] + L @ z_t
    port_returns_t = sim_returns_t.T @ weights_arr
    
    # --- Calculate VaR & CVaR ---
    # Normal distribution metrics
    var_95_norm_pct = -np.percentile(port_returns_normal, 5)
    var_99_norm_pct = -np.percentile(port_returns_normal, 1)
    
    var_95_norm_usd = var_95_norm_pct * portfolio_value
    var_99_norm_usd = var_99_norm_pct * portfolio_value
    
    losses_95_norm = port_returns_normal[port_returns_normal <= -var_95_norm_pct]
    losses_99_norm = port_returns_normal[port_returns_normal <= -var_99_norm_pct]
    
    cvar_95_norm_pct = -np.mean(losses_95_norm) if len(losses_95_norm) > 0 else var_95_norm_pct
    cvar_99_norm_pct = -np.mean(losses_99_norm) if len(losses_99_norm) > 0 else var_99_norm_pct
    
    cvar_95_norm_usd = cvar_95_norm_pct * portfolio_value
    cvar_99_norm_usd = cvar_99_norm_pct * portfolio_value
    
    # Student-t distribution metrics
    var_95_t_pct = -np.percentile(port_returns_t, 5)
    var_99_t_pct = -np.percentile(port_returns_t, 1)
    
    var_95_t_usd = var_95_t_pct * portfolio_value
    var_99_t_usd = var_99_t_pct * portfolio_value
    
    losses_95_t = port_returns_t[port_returns_t <= -var_95_t_pct]
    losses_99_t = port_returns_t[port_returns_t <= -var_99_t_pct]
    
    cvar_95_t_pct = -np.mean(losses_95_t) if len(losses_95_t) > 0 else var_95_t_pct
    cvar_99_t_pct = -np.mean(losses_99_t) if len(losses_99_t) > 0 else var_99_t_pct
    
    cvar_95_t_usd = cvar_95_t_pct * portfolio_value
    cvar_99_t_usd = cvar_99_t_pct * portfolio_value
    
    # Prepare simulated distributions for histogram plotting
    # We downsample the plotted returns (e.g. keep 1000 points or bin counts) to keep JSON response sizes reasonable,
    # or just return the raw values if we want full fidelity. Returning 2,000 values is standard and light.
    sample_indices = np.linspace(0, n_sims - 1, 2000, dtype=int)
    plot_returns_normal = port_returns_normal[sample_indices].tolist()
    plot_returns_t = port_returns_t[sample_indices].tolist()
    
    return {
        "normal": {
            "var_95_1d_pct": float(var_95_norm_pct),
            "var_99_1d_pct": float(var_99_norm_pct),
            "var_95_1d_usd": float(var_95_norm_usd),
            "var_99_1d_usd": float(var_99_norm_usd),
            "cvar_95_1d_pct": float(cvar_95_norm_pct),
            "cvar_99_1d_pct": float(cvar_99_norm_pct),
            "cvar_95_1d_usd": float(cvar_95_norm_usd),
            "cvar_99_1d_usd": float(cvar_99_norm_usd),
            "sim_returns_sample": plot_returns_normal
        },
        "student_t": {
            "df": student_t_df,
            "var_95_1d_pct": float(var_95_t_pct),
            "var_99_1d_pct": float(var_99_t_pct),
            "var_95_1d_usd": float(var_95_t_usd),
            "var_99_1d_usd": float(var_99_t_usd),
            "cvar_95_1d_pct": float(cvar_95_t_pct),
            "cvar_99_1d_pct": float(cvar_99_t_pct),
            "cvar_95_1d_usd": float(cvar_95_t_usd),
            "cvar_99_1d_usd": float(cvar_99_t_usd),
            "sim_returns_sample": plot_returns_t
        }
    }
