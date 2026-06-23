from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional

class PortfolioValidateRequest(BaseModel):
    tickers: List[str] = Field(..., description="List of ticker symbols")
    weights: List[float] = Field(..., description="List of weights corresponding to tickers")

    @field_validator("tickers")
    @classmethod
    def validate_tickers(cls, v):
        if not v:
            raise ValueError("Tickers list cannot be empty.")
        return [t.upper().strip() for t in v]

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, v, info):
        if not v:
            raise ValueError("Weights list cannot be empty.")
        # Check sum is close to 1.0 (within 1%)
        if not abs(sum(v) - 1.0) < 0.01:
            raise ValueError("Weights must sum to 1.0 (or 100%).")
        return v

class RiskComputeRequest(BaseModel):
    tickers: List[str] = Field(..., description="List of ticker symbols")
    weights: List[float] = Field(..., description="List of weights corresponding to tickers")
    portfolio_value: float = Field(10000000.0, description="Total portfolio value in USD")
    lookback_days: int = Field(504, description="Lookback window in trading days")
    shocks: Dict[str, float] = Field(
        default_factory=lambda: {"vix": 0.50, "y10": 0.02, "oil": -0.20, "usd": 0.05},
        description="Hypothetical factor shocks (native units, e.g. 0.50 = +50% VIX)"
    )
    risk_free_rate: float = Field(0.04, description="Risk free rate for Sharpe ratio calculation")

    @field_validator("tickers")
    @classmethod
    def validate_tickers(cls, v):
        if not v:
            raise ValueError("Tickers list cannot be empty.")
        return [t.upper().strip() for t in v]

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, v, info):
        if not v:
            raise ValueError("Weights list cannot be empty.")
        if not abs(sum(v) - 1.0) < 0.01:
            raise ValueError("Weights must sum to 1.0 (or 100%).")
        return v

class ReportGenerateRequest(RiskComputeRequest):
    charts: Optional[Dict[str, str]] = Field(
        None, 
        description="Optional base64 PNG data-URIs for charts, keys: 'pnl_dist', 'drawdowns'"
    )
    name: Optional[str] = Field(None, description="Optional customer/manager name")
    age: Optional[int] = Field(None, description="Optional customer/manager age")

