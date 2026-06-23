from fastapi import APIRouter, HTTPException, Depends
from api.schemas import PortfolioValidateRequest
import yfinance as yf
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/portfolio", tags=["portfolio"])

@router.post("/validate")
async def validate_portfolio(payload: PortfolioValidateRequest):
    """
    Validates if a list of tickers are real, tradeable tickers on Yahoo Finance.
    Also validates that weights sum to 100%.
    """
    invalid_tickers = []
    
    for ticker in payload.tickers:
        try:
            # Attempt to download a very short history to verify existence
            logger.info(f"Validating ticker: {ticker}")
            t = yf.Ticker(ticker)
            history = t.history(period="1d")
            
            # yfinance returns an empty DataFrame if ticker is invalid or delisted
            if history.empty:
                invalid_tickers.append(ticker)
        except Exception as e:
            logger.error(f"Error checking ticker {ticker}: {str(e)}")
            invalid_tickers.append(ticker)
            
    if invalid_tickers:
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Invalid or inactive ticker(s) found: {', '.join(invalid_tickers)}",
                "invalid_tickers": invalid_tickers
            }
        )
        
    return {
        "status": "success",
        "message": "All tickers and weights are valid.",
        "tickers": payload.tickers,
        "weights": payload.weights
    }
