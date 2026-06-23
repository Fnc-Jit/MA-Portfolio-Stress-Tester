import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch
from risk_engine.historical_replay import run_historical_replay

def test_historical_replay_calculation():
    """
    Test historical replay calculations using a mocked returns series.
    """
    # Create mock daily returns for 2 assets over 5 days
    # Day 1: Asset A +1%, Asset B -1%
    # Day 2: Asset A -2%, Asset B -3%
    # Day 3: Asset A +1.5%, Asset B +2%
    # Day 4: Asset A -5%, Asset B -10%
    # Day 5: Asset A +1%, Asset B +1%
    dates = pd.date_range(start="2008-09-15", periods=5)
    mock_returns = pd.DataFrame({
        "A": [0.01, -0.02, 0.015, -0.05, 0.01],
        "B": [-0.01, -0.03, 0.02, -0.10, 0.01]
    }, index=dates)
    
    tickers = ["A", "B"]
    weights = [0.6, 0.4]  # Portfolio = 60% A, 40% B
    
    # Portfolio daily returns:
    # Day 1: 0.6*(0.01) + 0.4*(-0.01) = 0.006 - 0.004 = 0.002 (+0.2%)
    # Day 2: 0.6*(-0.02) + 0.4*(-0.03) = -0.012 - 0.012 = -0.024 (-2.4%)
    # Day 3: 0.6*(0.015) + 0.4*(0.02) = 0.009 + 0.008 = 0.017 (+1.7%)
    # Day 4: 0.6*(-0.05) + 0.4*(-0.10) = -0.03 - 0.04 = -0.070 (-7.0%)
    # Day 5: 0.6*(0.01) + 0.4*(0.01) = 0.010 (+1.0%)
    
    expected_daily_returns = np.array([0.002, -0.024, 0.017, -0.07, 0.01])
    
    # Compounded values (starting at 1.0):
    # Day 1: 1.0 * 1.002 = 1.0020
    # Day 2: 1.002 * (1 - 0.024) = 1.002 * 0.976 = 0.977952
    # Day 3: 0.977952 * (1 + 0.017) = 0.977952 * 1.017 = 0.994577
    # Day 4: 0.994577 * (1 - 0.07) = 0.994577 * 0.93 = 0.924957
    # Day 5: 0.924957 * (1 + 0.01) = 0.924957 * 1.01 = 0.934206
    
    # Peak values:
    # Day 1: Max = 1.0020
    # Day 2: Max = 1.0020. DD = 0.977952 / 1.002 - 1 = -0.024 (-2.4%)
    # Day 3: Max = 1.0020. DD = 0.994577 / 1.002 - 1 = -0.0074 (-0.74%)
    # Day 4: Max = 1.0020. DD = 0.924957 / 1.002 - 1 = -0.07689 (-7.69%)
    # Day 5: Max = 1.0020. DD = 0.934206 / 1.002 - 1 = -0.0676 (-6.76%)
    # Worst Drawdown should be approx -7.69% (at Day 4)
    # Worst day is Day 4 (-7.0%)
    # Final return is 0.934206 - 1 = -0.06579 (-6.58%)
    
    # Patch get_crisis_window_returns to return our mock returns
    with patch("risk_engine.historical_replay.get_crisis_window_returns", return_value=mock_returns) as mock_fetch:
        results = run_historical_replay(tickers, weights, "gfc_2008")
        
        mock_fetch.assert_called_once_with(tickers, "gfc_2008")
        
        assert results["crisis_name"] == "gfc_2008"
        assert np.isclose(results["worst_day"], -0.07)
        assert results["worst_day_date"] == dates[3].strftime("%Y-%m-%d")
        
        assert np.isclose(results["final_return"], 0.93420624 - 1.0)
        assert np.isclose(results["max_drawdown"], (0.924957184 / 1.0020) - 1.0)
        
        # Check returns path length
        assert len(results["returns_path"]) == 5
        assert results["returns_path"][0]["date"] == dates[0].strftime("%Y-%m-%d")
        assert np.isclose(results["returns_path"][0]["value"], 0.002)
