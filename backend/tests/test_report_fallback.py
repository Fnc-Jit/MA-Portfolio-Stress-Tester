import pytest
import os
import tempfile
from unittest.mock import patch
from risk_engine.report import generate_pdf_report, generate_html_report

def test_report_html_fallback():
    """
    Test that generate_pdf_report successfully falls back to writing an HTML report
    when WEASYPRINT_AVAILABLE is mocked as False.
    """
    # Create simple mock report data
    mock_data = {
        "portfolio_value": 5000000.0,
        "lookback_days": 252,
        "parametric": {
            "var_95_1d_usd": 120000.0,
            "var_95_1d_pct": 0.024,
            "var_99_1d_usd": 180000.0,
            "var_99_1d_pct": 0.036,
            "cvar_95_1d_usd": 150000.0,
            "cvar_95_1d_pct": 0.030,
            "annualized_vol": 0.18,
            "asset_metrics": []
        },
        "monte_carlo": {
            "normal": {
                "var_95_1d_usd": 122000.0,
                "var_95_1d_pct": 0.0244,
                "cvar_95_1d_usd": 152000.0,
                "cvar_95_1d_pct": 0.0304
            },
            "student_t": {
                "var_95_1d_usd": 140000.0,
                "var_95_1d_pct": 0.028,
                "cvar_95_1d_usd": 180000.0,
                "cvar_95_1d_pct": 0.036
            }
        },
        "general_metrics": {
            "sharpe_ratio": 1.25
        },
        "factor_shocks": {
            "factor_impacts": [],
            "portfolio_projected_return": -0.015,
            "portfolio_projected_usd": -75000.0
        },
        "agreement": {
            "fat_tail_presence": "LOW",
            "explanation": "Test explanation"
        },
        "crises": [],
        "charts": None
    }
    
    temp_dir = tempfile.gettempdir()
    output_pdf_path = os.path.join(temp_dir, "test_risk_report.pdf")
    expected_html_path = os.path.join(temp_dir, "test_risk_report.pdf.html")
    
    # Remove existing files if any
    if os.path.exists(output_pdf_path): os.remove(output_pdf_path)
    if os.path.exists(expected_html_path): os.remove(expected_html_path)
    
    # Mock WEASYPRINT_AVAILABLE to be False to force the HTML fallback
    with patch("risk_engine.report.WEASYPRINT_AVAILABLE", False):
        result = generate_pdf_report(mock_data, output_pdf_path)
        
        # Verify it returns False (indicating HTML fallback occurred)
        assert result is False
        
        # Verify the PDF file does not exist, but the HTML fallback file does
        assert not os.path.exists(output_pdf_path)
        assert os.path.exists(expected_html_path)
        
        # Read HTML content and verify it contains key information
        with open(expected_html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            assert "PORTFOLIO STRESS TEST & RISK REPORT" in html_content
            assert "$5,000,000.00" in html_content
            assert "$120,000.00" in html_content
            assert "1.25" in html_content
            
    # Clean up fallback file
    if os.path.exists(expected_html_path):
        os.remove(expected_html_path)
