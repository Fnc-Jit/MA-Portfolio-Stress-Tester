import os
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf
from fredapi import Fred

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent / "data_cache"
CACHE_DIR.mkdir(exist_ok=True)

CRISIS_WINDOWS = {
    "gfc_2008":      ("2008-09-01", "2009-03-31"),
    "covid_2020":    ("2020-02-01", "2020-04-30"),
    "taper_2013":    ("2013-05-01", "2013-09-30"),
    "hike_2022":     ("2022-01-01", "2022-10-31"),
}

def fetch_prices(tickers: list[str], start: str = "2005-01-01", end: str | None = None) -> pd.DataFrame:
    """
    Pull daily adjusted close prices for all tickers, cache to parquet, and return a wide DataFrame.
    Throws ValueError if tickers are invalid or no data is returned.
    """
    if not tickers:
        raise ValueError("Ticker list cannot be empty.")
    
    # Sort tickers to make cache key deterministic
    sorted_tickers = sorted([t.upper().strip() for t in tickers])
    end_str = end if end else "today"
    cache_key = f"prices_{'_'.join(sorted_tickers)}_{start}_{end_str}.parquet"
    cache_path = CACHE_DIR / cache_key
    
    if cache_path.exists():
        logger.info(f"Loading prices from cache: {cache_path.name}")
        return pd.read_parquet(cache_path)
    
    logger.info(f"Downloading prices for {sorted_tickers} from {start} to {end_str}")
    # Use yfinance download
    try:
        # Fetching Close prices. Under yfinance v1.4.1+, group_by='column' is default
        raw_data = yf.download(sorted_tickers, start=start, end=end, progress=False)
        
        if raw_data.empty:
            raise ValueError(f"No data returned for tickers {sorted_tickers} in the specified date range.")
            
        # Inspect columns. Adjust for multi-index if downloading multiple tickers
        if isinstance(raw_data.columns, pd.MultiIndex):
            if "Close" in raw_data.columns.levels[0]:
                prices = raw_data["Close"]
            elif "Adj Close" in raw_data.columns.levels[0]:
                prices = raw_data["Adj Close"]
            else:
                raise ValueError("Could not find Close or Adj Close prices in yfinance output.")
        else:
            # Single ticker download or flat columns
            if "Close" in raw_data.columns:
                prices = raw_data[["Close"]]
                prices.columns = sorted_tickers
            elif "Adj Close" in raw_data.columns:
                prices = raw_data[["Adj Close"]]
                prices.columns = sorted_tickers
            else:
                prices = raw_data
                
        # Double check that we have all tickers as columns
        missing_tickers = [t for t in sorted_tickers if t not in prices.columns]
        if missing_tickers:
            raise ValueError(f"Failed to fetch data for ticker(s): {', '.join(missing_tickers)}")
            
        # Standardize index
        prices.index = pd.to_datetime(prices.index)
        prices = prices[sorted_tickers]  # Keep specified order
        
        # Check for empty columns or all-NaNs
        for ticker in sorted_tickers:
            if prices[ticker].isna().all():
                raise ValueError(f"Ticker '{ticker}' contains only missing values.")
                
        # Forward fill up to 5 consecutive days of missing prices (e.g. holidays), then backward fill
        prices = prices.ffill(limit=5).bfill()
        
        # Save to cache
        prices.to_parquet(cache_path)
        return prices
        
    except Exception as e:
        logger.error(f"Error fetching prices: {str(e)}")
        raise ValueError(f"Error fetching prices from yfinance: {str(e)}")

def generate_synthetic_macro(dates: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Generate realistic synthetic macro factors matching the given date index.
    Used as a fallback when FRED API key is missing or calls fail.
    """
    logger.warning("Using synthetic macro factors as fallback.")
    n_days = len(dates)
    np.random.seed(42)  # For reproducibility
    
    # 1. VIX (Mean reverting style log-normal)
    # Target mean ~18, sd ~6
    vix = np.zeros(n_days)
    vix[0] = 16.0
    for i in range(1, n_days):
        # Mean reversion: vix_t = vix_{t-1} + speed*(mean - vix_{t-1}) + noise
        noise = np.random.normal(0, 1.5)
        vix[i] = max(9.0, vix[i-1] + 0.05 * (18.0 - vix[i-1]) + noise)
        
    # 2. 10Y Yield DGS10 (Random walk with drift around 3.5%)
    y10 = np.zeros(n_days)
    y10[0] = 3.5
    for i in range(1, n_days):
        noise = np.random.normal(0, 0.04)
        # Drift toward 3.5%
        y10[i] = max(0.1, y10[i-1] + 0.02 * (3.5 - y10[i-1]) + noise)
        
    # 3. Oil Price DCOILWTICO (Random walk around $70)
    oil = np.zeros(n_days)
    oil[0] = 72.0
    for i in range(1, n_days):
        noise = np.random.normal(0, 1.2)
        oil[i] = max(10.0, oil[i-1] + 0.01 * (70.0 - oil[i-1]) + noise)
        
    # 4. USD Index DTWEXBGS / DTWEXAFEGS (Random walk around 100)
    usd = np.zeros(n_days)
    usd[0] = 98.0
    for i in range(1, n_days):
        noise = np.random.normal(0, 0.4)
        usd[i] = max(50.0, usd[i-1] + 0.01 * (100.0 - usd[i-1]) + noise)
        
    df = pd.DataFrame({
        "vix": vix,
        "y10": y10,
        "oil": oil,
        "usd": usd
    }, index=dates)
    
    return df

def fetch_macro_factors(fred_api_key: str | None = None, start: str = "2005-01-01", target_dates: pd.DatetimeIndex | None = None) -> pd.DataFrame:
    """
    Fetch VIX, 10Y yield, WTI oil, and USD index from FRED.
    Falls back to synthetic generation if FRED API key is missing or calls fail.
    """
    api_key = fred_api_key or os.getenv("FRED_API_KEY")
    
    # If target_dates is not provided, make a default range
    if target_dates is None:
        target_dates = pd.date_range(start=start, end=pd.Timestamp.now(), freq='B')
        
    if not api_key:
        logger.warning("No FRED API key provided. Falling back to synthetic macro generation.")
        return generate_synthetic_macro(target_dates)
        
    # Try fetching from FRED
    cache_key = f"macro_{start}.parquet"
    cache_path = CACHE_DIR / cache_key
    
    if cache_path.exists():
        logger.info(f"Loading macro factors from cache: {cache_path.name}")
        df = pd.read_parquet(cache_path)
        # Reindex to match target_dates if provided
        return df.reindex(target_dates).ffill().bfill()
        
    try:
        logger.info("Connecting to FRED to download macro factors...")
        fred = Fred(api_key=api_key)
        series = {
            "vix":   "VIXCLS",       # VIX Index
            "y10":   "DGS10",        # 10-Year Treasury Constant Maturity Rate
            "oil":   "DCOILWTICO",   # Crude Oil Prices: Brent/WTI
            "usd":   "DTWEXBGS",     # Trade Weighted U.S. Dollar Index (Older/Broad)
        }
        
        data_dict = {}
        for name, code in series.items():
            try:
                s = fred.get_series(code, start)
                s.index = pd.to_datetime(s.index)
                data_dict[name] = s
            except Exception as e:
                logger.warning(f"Failed to fetch {name} ({code}) from FRED: {str(e)}. Attempting alternatives...")
                # Fallback series codes in case codes change or are missing
                if name == "usd":
                    try:
                        s = fred.get_series("DTWEXAFEGS", start)  # Alternate USD index
                        s.index = pd.to_datetime(s.index)
                        data_dict[name] = s
                        continue
                    except:
                        pass
                raise e
                
        df = pd.DataFrame(data_dict)
        # Check if empty
        if df.dropna(how='all').empty:
            raise ValueError("FRED returned empty dataframe.")
            
        # Clean FRED data (FRED has data points on holidays but with '.' or NaN)
        df = df.apply(pd.to_numeric, errors='coerce')
        df = df.ffill().bfill()
        
        # Save raw to cache
        df.to_parquet(cache_path)
        
        # Reindex to target_dates
        df_reindexed = df.reindex(target_dates).ffill().bfill()
        return df_reindexed
        
    except Exception as e:
        logger.error(f"Error fetching from FRED API: {str(e)}. Falling back to synthetic macro factors.")
        return generate_synthetic_macro(target_dates)

def get_crisis_window_returns(tickers: list[str], crisis_name: str) -> pd.DataFrame:
    """
    Return daily simple returns for tickers during a named historical crisis window.
    Throws ValueError if the window has no overlap with ticker history or errors out.
    """
    if crisis_name not in CRISIS_WINDOWS:
        raise ValueError(f"Unknown crisis name: {crisis_name}. Available: {list(CRISIS_WINDOWS.keys())}")
        
    start, end = CRISIS_WINDOWS[crisis_name]
    logger.info(f"Fetching crisis window '{crisis_name}' ({start} to {end}) for {tickers}")
    
    # Download prices specifically for this window
    prices = fetch_prices(tickers, start=start, end=end)
    
    # Check if we got enough dates
    if len(prices) < 5:
        raise ValueError(f"Too few observations ({len(prices)}) in crisis window '{crisis_name}' for tickers {tickers}.")
        
    # Calculate simple returns
    returns = prices.pct_change().dropna()
    return returns
