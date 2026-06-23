import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from risk_engine.data_loader import fetch_macro_factors, generate_synthetic_macro, fetch_prices

def test_fetch_macro_factors_synthetic_fallback():
    """
    Test that fetch_macro_factors falls back to synthetic generation
    when no FRED API key is provided and environment variable is unset.
    """
    target_dates = pd.date_range(start="2023-01-01", periods=10, freq="B")
    
    # 1. Clear environment variable if set to force fallback
    with patch.dict("os.environ", {}, clear=True):
        df_macro = fetch_macro_factors(fred_api_key=None, target_dates=target_dates)
        
        # Verify dataframe structure and dimensions
        assert isinstance(df_macro, pd.DataFrame)
        assert len(df_macro) == 10
        assert list(df_macro.columns) == ["vix", "y10", "oil", "usd"]
        
        # Verify index matches target_dates
        pd.testing.assert_index_equal(df_macro.index, target_dates)
        
        # Check that values are within reasonable parameters (synthetic generation boundaries)
        assert df_macro["vix"].min() >= 9.0
        assert df_macro["y10"].min() >= 0.1
        assert df_macro["oil"].min() >= 10.0
        assert df_macro["usd"].min() >= 50.0

@patch("risk_engine.data_loader.Fred")
def test_fetch_macro_factors_with_mock_api(mock_fred_class):
    """
    Test that fetch_macro_factors correctly queries the FRED API when a key is provided
    and handles success.
    """
    # Mock the Fred instance behavior
    mock_fred_instance = MagicMock()
    mock_fred_class.return_value = mock_fred_instance
    
    dates = pd.date_range(start="2023-01-01", periods=5, freq="B")
    # FRED returns pandas Series
    vix_series = pd.Series([15.0, 16.0, 14.5, 15.2, 16.1], index=dates)
    y10_series = pd.Series([3.5, 3.55, 3.48, 3.52, 3.61], index=dates)
    oil_series = pd.Series([75.0, 76.2, 74.8, 75.5, 77.1], index=dates)
    usd_series = pd.Series([101.0, 101.5, 100.8, 101.2, 102.1], index=dates)
    
    def mock_get_series(code, start):
        if code == "VIXCLS": return vix_series
        if code == "DGS10": return y10_series
        if code == "DCOILWTICO": return oil_series
        if code == "DTWEXBGS": return usd_series
        raise ValueError("Unknown series code")
        
    mock_fred_instance.get_series.side_effect = mock_get_series
    
    # Call fetch_macro_factors with a mock key
    df_macro = fetch_macro_factors(fred_api_key="mock_key_123", target_dates=dates)
    
    # Assert data loader queried FRED
    assert mock_fred_class.called
    assert df_macro.shape == (5, 4)
    assert np.isclose(df_macro["vix"].iloc[0], 15.0)
    assert np.isclose(df_macro["y10"].iloc[4], 3.61)

@patch("risk_engine.data_loader.Fred")
def test_fetch_macro_factors_api_failure_fallback(mock_fred_class):
    """
    Test that fetch_macro_factors falls back to synthetic generation
    if the FRED API throws an exception.
    """
    mock_fred_instance = MagicMock()
    mock_fred_class.return_value = mock_fred_instance
    mock_fred_instance.get_series.side_effect = Exception("API Limit Exceeded")
    
    target_dates = pd.date_range(start="2023-01-01", periods=5, freq="B")
    
    df_macro = fetch_macro_factors(fred_api_key="faulty_key", target_dates=target_dates)
    
    # Ensure it didn't raise, and returned synthetic fallback data matching target_dates
    assert isinstance(df_macro, pd.DataFrame)
    assert len(df_macro) == 5
    pd.testing.assert_index_equal(df_macro.index, target_dates)
