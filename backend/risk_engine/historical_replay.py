import numpy as np
import pandas as pd
from typing import Dict, Any, List
import logging
from risk_engine.data_loader import get_crisis_window_returns, CRISIS_WINDOWS

logger = logging.getLogger(__name__)

def run_historical_replay(tickers: list[str], weights: list[float], crisis_name: str) -> Dict[str, Any]:
    """
    Replays a specific historical crisis window against the current portfolio weights.
    Returns metrics (max drawdown, final return, worst day) and the timeseries cumulative return path.
    """
    # Validate weights
    if len(tickers) != len(weights):
        raise ValueError("Number of tickers must match number of weights.")
    if not np.isclose(sum(weights), 1.0):
        raise ValueError("Weights must sum to 1.0 (or close to it).")
        
    weights_arr = np.array(weights)
    
    try:
        # Fetch daily returns for tickers in the crisis window
        df_returns = get_crisis_window_returns(tickers, crisis_name)
        
        # Calculate daily portfolio returns: R_p,t = w^T R_t
        # df_returns.values is shape (T, N)
        # weights_arr is shape (N,)
        portfolio_daily_returns = df_returns.values @ weights_arr
        
        # Convert to pandas Series for easier indexing/timeseries calculation
        port_returns_series = pd.Series(portfolio_daily_returns, index=df_returns.index)
        
        # Cumulative return path (starting from 1.0)
        # Cumulative value = \prod (1 + R_p,t)
        cumulative_value = (1 + port_returns_series).cumprod()
        # Cumulative returns = cumulative value - 1.0
        cumulative_returns = cumulative_value - 1.0
        
        # Calculate Drawdown: Value_t / Max_Value_t - 1
        running_max = cumulative_value.cummax()
        # Handle cases where running_max is <= 0 (very unlikely unless we lose 100% of portfolio)
        running_max = np.maximum(running_max, 1e-8)
        drawdowns = (cumulative_value / running_max) - 1.0
        max_drawdown = drawdowns.min()
        
        # Worst single-day performance
        worst_day = port_returns_series.min()
        worst_day_date = port_returns_series.idxmin().strftime("%Y-%m-%d")
        
        # Final cumulative return
        final_return = cumulative_value.iloc[-1] - 1.0
        
        # Format the returns path for JSON/Plotly charting
        returns_path = [
            {"date": date.strftime("%Y-%m-%d"), "value": float(val)}
            for date, val in cumulative_returns.items()
        ]
        
        start_date, end_date = CRISIS_WINDOWS[crisis_name]
        
        return {
            "crisis_name": crisis_name,
            "start_date": start_date,
            "end_date": end_date,
            "max_drawdown": float(max_drawdown),
            "worst_day": float(worst_day),
            "worst_day_date": worst_day_date,
            "final_return": float(final_return),
            "returns_path": returns_path
        }
        
    except Exception as e:
        logger.error(f"Error in running historical replay for {crisis_name}: {str(e)}")
        # Return a soft failure structure with placeholders or empty fields if ticker did not exist then
        start_date, end_date = CRISIS_WINDOWS.get(crisis_name, ("unknown", "unknown"))
        return {
            "crisis_name": crisis_name,
            "start_date": start_date,
            "end_date": end_date,
            "max_drawdown": 0.0,
            "worst_day": 0.0,
            "worst_day_date": "",
            "final_return": 0.0,
            "returns_path": [],
            "error": f"Failed to run: {str(e)}"
        }

def run_all_historical_replays(tickers: list[str], weights: list[float]) -> Dict[str, Dict[str, Any]]:
    """
    Runs historical replay for all predefined crisis windows.
    """
    results = {}
    for crisis_name in CRISIS_WINDOWS.keys():
        results[crisis_name] = run_historical_replay(tickers, weights, crisis_name)
    return results
