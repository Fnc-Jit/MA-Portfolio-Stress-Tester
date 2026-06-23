from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
import tempfile
import os
import logging
from typing import Dict, Any

from api.schemas import RiskComputeRequest, ReportGenerateRequest
import risk_engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/risk", tags=["risk"])

def perform_risk_computations(payload: RiskComputeRequest) -> Dict[str, Any]:
    """
    Common helper to perform all risk engine calculations for a given portfolio.
    """
    tickers = payload.tickers
    weights = payload.weights
    port_val = payload.portfolio_value
    lookback = payload.lookback_days
    shocks = payload.shocks
    rf_rate = payload.risk_free_rate

    try:
        # 1. Fetch prices
        prices = risk_engine.fetch_prices(tickers, start="2005-01-01")
        
        # 2. Fetch FRED macro factors (aligned to the target dates of the lookback prices)
        # Fetch lookback subset of prices first to get target dates
        df_lookback_prices = prices.tail(lookback)
        macro_factors = risk_engine.fetch_macro_factors(
            start="2005-01-01", 
            target_dates=df_lookback_prices.index
        )
        
        # 3. Parametric VaR
        parametric_results = risk_engine.calculate_parametric_var(
            prices=prices,
            weights=weights,
            portfolio_value=port_val,
            lookback_days=lookback
        )
        
        # 4. Monte Carlo VaR (normal & Student-t)
        mc_results = risk_engine.run_monte_carlo_simulation(
            prices=prices,
            weights=weights,
            portfolio_value=port_val,
            lookback_days=lookback,
            n_sims=10000,
            student_t_df=5
        )
        
        # 5. Historical Replays
        historical_results = risk_engine.run_all_historical_replays(
            tickers=tickers,
            weights=weights
        )
        
        # 6. Factor Shock Analysis
        factor_shock_results = risk_engine.run_factor_shock_analysis(
            prices=prices,
            macro_factors=macro_factors,
            weights=weights,
            shocks=shocks,
            portfolio_value=port_val,
            lookback_days=lookback
        )
        
        # 7. General Portfolio Performance Metrics (Volatility, Sharpe, drawdown over entire price history)
        general_metrics = risk_engine.calculate_portfolio_metrics(
            prices=prices,
            weights=weights,
            risk_free_rate=rf_rate
        )
        
        # 8. Model Agreement Check
        agreement = risk_engine.check_model_agreement(
            parametric_var=parametric_results["var_95_1d_usd"],
            monte_carlo_normal_var=mc_results["normal"]["var_95_1d_usd"],
            monte_carlo_t_var=mc_results["student_t"]["var_95_1d_usd"]
        )
        
        return {
            "portfolio_value": port_val,
            "lookback_days": lookback,
            "general_metrics": general_metrics,
            "parametric": parametric_results,
            "monte_carlo": mc_results,
            "historical_replays": historical_results,
            "factor_shocks": factor_shock_results,
            "agreement": agreement
        }
        
    except Exception as e:
        logger.error(f"Error executing risk computations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Risk engine error: {str(e)}")

@router.post("/compute")
async def compute_portfolio_risk(payload: RiskComputeRequest):
    """
    Executes historical replay, parametric VaR, Monte Carlo, and factor-shock models
    for the specified portfolio and parameters.
    """
    results = perform_risk_computations(payload)
    return results

@router.post("/report")
async def generate_risk_report(payload: ReportGenerateRequest):
    """
    Computes portfolio risk parameters, renders a PDF risk memo, and returns it.
    If WeasyPrint is not installed or fails, falls back to sending a print-friendly HTML page.
    """
    # 1. Re-run risk metrics
    results = perform_risk_computations(payload)
    
    # 2. Add extra fields needed for HTML/PDF template
    report_data = {
        "portfolio_value": results["portfolio_value"],
        "lookback_days": results["lookback_days"],
        "parametric": results["parametric"],
        "monte_carlo": results["monte_carlo"],
        "general_metrics": results["general_metrics"],
        "factor_shocks": results["factor_shocks"],
        "agreement": results["agreement"],
        "crises": list(results["historical_replays"].values()),
        "charts": payload.charts  # Inject client side base64 Plotly PNGs if sent
    }
    
    # Create a temporary file
    temp_dir = tempfile.gettempdir()
    temp_filename = next(tempfile._get_candidate_names())
    
    try:
        # Check if WeasyPrint is available
        from risk_engine.report import WEASYPRINT_AVAILABLE
        
        if WEASYPRINT_AVAILABLE:
            pdf_path = os.path.join(temp_dir, f"{temp_filename}.pdf")
            success = risk_engine.report.generate_pdf_report(report_data, pdf_path)
            if success and os.path.exists(pdf_path):
                return FileResponse(
                    path=pdf_path,
                    media_type="application/pdf",
                    filename="portfolio_risk_report.pdf"
                )
                
        # Fallback to HTML file download/display
        html_path = os.path.join(temp_dir, f"{temp_filename}.html")
        risk_engine.report.generate_pdf_report(report_data, html_path)
        return FileResponse(
            path=html_path,
            media_type="text/html",
            filename="portfolio_risk_report.html"
        )
        
    except Exception as e:
        logger.error(f"Failed to generate report file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Report rendering error: {str(e)}")
