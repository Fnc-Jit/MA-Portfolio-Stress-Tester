import numpy as np
import pandas as pd
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def calculate_portfolio_metrics(
    prices: pd.DataFrame,
    weights: list[float],
    risk_free_rate: float = 0.04
) -> Dict[str, Any]:
    """
    Computes general portfolio stats: Sharpe, max drawdown, and annualized volatility
    over the entire available history of the prices DataFrame.
    """
    if len(weights) != prices.shape[1]:
        raise ValueError("Weights must match number of assets.")
        
    weights_arr = np.array(weights)
    
    # Calculate daily returns
    returns = prices.pct_change().dropna()
    
    # Daily portfolio returns
    port_returns = returns.values @ weights_arr
    port_returns_series = pd.Series(port_returns, index=returns.index)
    
    # Annualized volatility
    daily_vol = port_returns_series.std()
    annualized_vol = daily_vol * np.sqrt(252)
    
    # Annualized return (compounded)
    # E.g. (total return + 1) ** (252 / T) - 1
    n_days = len(port_returns_series)
    if n_days == 0:
        return {
            "annualized_volatility": 0.0,
            "annualized_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0
        }
        
    total_return = (1 + port_returns_series).prod() - 1.0
    annualized_return = (total_return + 1.0) ** (252.0 / n_days) - 1.0
    
    # Sharpe Ratio: (Annualized Return - Risk Free Rate) / Annualized Volatility
    if annualized_vol > 0:
        sharpe_ratio = (annualized_return - risk_free_rate) / annualized_vol
    else:
        sharpe_ratio = 0.0
        
    # Maximum Drawdown over the entire period
    cumulative_value = (1 + port_returns_series).cumprod()
    running_max = cumulative_value.cummax()
    running_max = np.maximum(running_max, 1e-8)
    drawdowns = (cumulative_value / running_max) - 1.0
    max_drawdown = drawdowns.min()
    
    return {
        "annualized_volatility": float(annualized_vol),
        "annualized_return": float(annualized_return),
        "sharpe_ratio": float(sharpe_ratio),
        "max_drawdown": float(max_drawdown)
    }

def check_model_agreement(
    parametric_var: float,
    monte_carlo_normal_var: float,
    monte_carlo_t_var: float,
    threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Compares the results of different VaR calculation methodologies.
    Highlights model divergence, which typically indicates non-normality (e.g. fat tails).
    """
    # Percentage difference between Parametric and MC Normal
    if parametric_var > 0:
        diff_mc_norm = abs(parametric_var - monte_carlo_normal_var) / parametric_var
        diff_mc_t = (monte_carlo_t_var - parametric_var) / parametric_var
    else:
        diff_mc_norm = 0.0
        diff_mc_t = 0.0
        
    # Determine agreement status
    # Normal simulation vs analytical should be very close (e.g. < 5% diff). If not, simulation might need more runs,
    # or lookback windows contain heavy non-normal assets (e.g., highly skewed, zero volatility).
    normal_agreement = "AGREE"
    if diff_mc_norm > threshold:
        normal_agreement = "DIVERGE_WARNING"
    if diff_mc_norm > (threshold * 2):
        normal_agreement = "DIVERGE_CRITICAL"
        
    # Student-t VaR relative to Parametric VaR (if t VaR is significantly higher, fat tails are present)
    fat_tail_presence = "LOW"
    if diff_mc_t > 0.10:
        fat_tail_presence = "MODERATE"
    if diff_mc_t > 0.25:
        fat_tail_presence = "HIGH"
        
    explanation = ""
    if fat_tail_presence == "HIGH":
        explanation = (
            "Monte Carlo Student-t VaR is substantially higher than Parametric VaR. "
            "This indicates strong fat-tailed behavior in your portfolio constituents, "
            "meaning large market drops happen much more frequently than a Normal distribution assumes. "
            "Parametric VaR is likely underestimating the true tail risk."
        )
    elif fat_tail_presence == "MODERATE":
        explanation = (
            "Monte Carlo Student-t VaR is moderately higher than Parametric VaR. "
            "Mild tail risks are present. Parametric VaR may slightly underestimate losses during extreme market stress."
        )
    else:
        explanation = (
            "Analytical (Parametric) and fat-tailed (Student-t) risk models are in close agreement. "
            "Asset returns follow standard distributions closely with no sign of major tail anomalies."
        )
        
    return {
        "diff_mc_normal": float(diff_mc_norm),
        "diff_mc_student_t": float(diff_mc_t),
        "normal_agreement": normal_agreement,
        "fat_tail_presence": fat_tail_presence,
        "explanation": explanation
    }
