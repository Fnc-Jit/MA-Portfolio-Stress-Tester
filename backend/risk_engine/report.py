import os
import logging
from typing import Dict, Any, List
import jinja2

logger = logging.getLogger(__name__)

# Try importing WeasyPrint, set a flag if missing
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception as e:
    logger.warning(f"WeasyPrint is not available: {str(e)}. PDF generation will fall back to HTML report output.")
    WEASYPRINT_AVAILABLE = False

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Portfolio Stress Test & Risk Report</title>
    <style>
        body {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: #333;
            line-height: 1.4;
            margin: 30px;
            background-color: #ffffff;
        }
        .header {
            border-bottom: 2px solid #1a365d;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }
        .header h1 {
            color: #1a365d;
            margin: 0;
            font-size: 26px;
            font-weight: 700;
        }
        .header .meta {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .section-title {
            color: #2b6cb0;
            font-size: 18px;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 5px;
            margin-top: 25px;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .grid-2 {
            display: table;
            width: 100%;
            margin-bottom: 15px;
        }
        .col {
            display: table-cell;
            width: 50%;
            vertical-align: top;
        }
        .col-left {
            padding-right: 15px;
        }
        .col-right {
            padding-left: 15px;
        }
        .kpi-card {
            background-color: #f7fafc;
            border: 1px solid #edf2f7;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 15px;
        }
        .kpi-title {
            font-size: 11px;
            text-transform: uppercase;
            color: #718096;
            margin-bottom: 5px;
            letter-spacing: 0.5px;
        }
        .kpi-value {
            font-size: 24px;
            font-weight: bold;
            color: #2d3748;
            font-family: monospace;
        }
        .kpi-value.risk-high {
            color: #e53e3e;
        }
        .kpi-value.risk-med {
            color: #dd6b20;
        }
        .kpi-value.risk-low {
            color: #38a169;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            font-size: 13px;
        }
        th {
            background-color: #edf2f7;
            color: #2d3748;
            text-align: left;
            padding: 8px 10px;
            font-weight: 600;
            border-bottom: 2px solid #cbd5e0;
        }
        td {
            padding: 8px 10px;
            border-bottom: 1px solid #e2e8f0;
        }
        tr:nth-child(even) td {
            background-color: #f8fafc;
        }
        .badge {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }
        .badge-red {
            background-color: #fed7d7;
            color: #9b2c2c;
        }
        .badge-orange {
            background-color: #feebc8;
            color: #9c4221;
        }
        .badge-green {
            background-color: #c6f6d5;
            color: #22543d;
        }
        .alert-box {
            border-left: 4px solid #3182ce;
            background-color: #ebf8ff;
            color: #2b6cb0;
            padding: 12px;
            border-radius: 0 4px 4px 0;
            font-size: 12px;
            margin-bottom: 20px;
        }
        .alert-box.alert-warning {
            border-left-color: #dd6b20;
            background-color: #fffaf0;
            color: #dd6b20;
        }
        .alert-box.alert-danger {
            border-left-color: #e53e3e;
            background-color: #fff5f5;
            color: #c53030;
        }
        .chart-img {
            max-width: 100%;
            height: auto;
            border: 1px solid #edf2f7;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        .bar-container {
            width: 100px;
            background-color: #e2e8f0;
            border-radius: 3px;
            height: 12px;
            display: inline-block;
            vertical-align: middle;
            margin-left: 10px;
        }
        .bar-fill {
            height: 100%;
            border-radius: 3px;
            background-color: #3182ce;
        }
        .bar-fill.red {
            background-color: #e53e3e;
        }
        .bar-fill.orange {
            background-color: #dd6b20;
        }
    </style>
</head>
<body>

    <div class="header">
        <h1>PORTFOLIO STRESS TEST & RISK REPORT</h1>
        <div class="meta">
            Generated: {{ date }} | Portfolio Value: ${{ "{:,.2f}".format(portfolio_value) }} | Lookback: {{ lookback_days }} days
            {% if name or age %}
            <br/>Prepared For: {% if name %}{{ name }}{% endif %}{% if age %} (Age: {{ age }}){% endif %}
            {% endif %}
        </div>
    </div>

    {% if agreement.fat_tail_presence != 'LOW' %}
    <div class="alert-box {% if agreement.fat_tail_presence == 'HIGH' %}alert-danger{% else %}alert-warning{% endif %}">
        <strong>Risk Modeling Alert:</strong> {{ agreement.explanation }}
    </div>
    {% endif %}

    <div class="section-title">Key Risk Metrics</div>
    <div class="grid-2">
        <div class="col col-left">
            <div class="kpi-card">
                <div class="kpi-title">1-Day 95% Parametric VaR</div>
                <div class="kpi-value risk-med">${{ "{:,.2f}".format(parametric.var_95_1d_usd) }} ({{ "{:.2%}".format(parametric.var_95_1d_pct) }})</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">1-Day 99% Parametric VaR</div>
                <div class="kpi-value risk-high">${{ "{:,.2f}".format(parametric.var_99_1d_usd) }} ({{ "{:.2%}".format(parametric.var_99_1d_pct) }})</div>
            </div>
        </div>
        <div class="col col-right">
            <div class="kpi-card">
                <div class="kpi-title">Annualized Volatility</div>
                <div class="kpi-value">${{ "{:.2%}".format(parametric.annualized_vol) }}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Expected Annual Sharpe Ratio</div>
                <div class="kpi-value {{ 'risk-low' if general_metrics.sharpe_ratio > 1.0 else 'risk-med' if general_metrics.sharpe_ratio > 0.0 else 'risk-high' }}">{{ "{:.2f}".format(general_metrics.sharpe_ratio) }}</div>
            </div>
        </div>
    </div>

    <div class="section-title">Portfolio Composition</div>
    <table>
        <thead>
            <tr>
                <th>Ticker</th>
                <th>Weight</th>
                <th>Daily Volatility</th>
                <th>Annualized Volatility</th>
                <th>Expected Return (Ann.)</th>
            </tr>
        </thead>
        <tbody>
            {% for asset in parametric.asset_metrics %}
            <tr>
                <td><strong>{{ asset.ticker }}</strong></td>
                <td>{{ "{:.1%}".format(asset.weight) }}</td>
                <td>{{ "{:.2%}".format(asset.daily_vol) }}</td>
                <td>{{ "{:.2%}".format(asset.annualized_vol) }}</td>
                <td>{{ "{:.2%}".format(asset.expected_return_annualized) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="section-title">Model Comparison: 1-Day Horizon</div>
    <table>
        <thead>
            <tr>
                <th>Methodology</th>
                <th>95% VaR (USD)</th>
                <th>95% VaR (%)</th>
                <th>95% CVaR / ES (USD)</th>
                <th>95% CVaR / ES (%)</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Parametric (Analytical)</strong></td>
                <td>${{ "{:,.2f}".format(parametric.var_95_1d_usd) }}</td>
                <td>{{ "{:.2%}".format(parametric.var_95_1d_pct) }}</td>
                <td>${{ "{:,.2f}".format(parametric.cvar_95_1d_usd) }}</td>
                <td>{{ "{:.2%}".format(parametric.cvar_95_1d_pct) }}</td>
            </tr>
            <tr>
                <td><strong>Monte Carlo (Normal)</strong></td>
                <td>${{ "{:,.2f}".format(monte_carlo.normal.var_95_1d_usd) }}</td>
                <td>{{ "{:.2%}".format(monte_carlo.normal.var_95_1d_pct) }}</td>
                <td>${{ "{:,.2f}".format(monte_carlo.normal.cvar_95_1d_usd) }}</td>
                <td>{{ "{:.2%}".format(monte_carlo.normal.cvar_95_1d_pct) }}</td>
            </tr>
            <tr>
                <td><strong>Monte Carlo (Student-t, df=5)</strong></td>
                <td>${{ "{:,.2f}".format(monte_carlo.student_t.var_95_1d_usd) }}</td>
                <td>{{ "{:.2%}".format(monte_carlo.student_t.var_95_1d_pct) }}</td>
                <td>${{ "{:,.2f}".format(monte_carlo.student_t.cvar_95_1d_usd) }}</td>
                <td>{{ "{:.2%}".format(monte_carlo.student_t.cvar_95_1d_pct) }}</td>
            </tr>
        </tbody>
    </table>

    <div class="section-title">Historical Crisis Replay</div>
    <table>
        <thead>
            <tr>
                <th>Crisis Event</th>
                <th>Window Dates</th>
                <th>Worst Daily Drop</th>
                <th>Max Drawdown</th>
                <th>Final Window P&amp;L (%)</th>
                <th>Final Window P&amp;L (USD)</th>
            </tr>
        </thead>
        <tbody>
            {% for crisis in crises %}
            <tr>
                <td><strong>{{ crisis.crisis_name.replace('_', ' ').upper() }}</strong></td>
                <td style="font-size: 11px; color:#666;">{{ crisis.start_date }} to {{ crisis.end_date }}</td>
                <td class="risk-high" style="font-weight:600;">{{ "{:.2%}".format(crisis.worst_day) }}</td>
                <td class="risk-high" style="font-weight:600;">{{ "{:.2%}".format(crisis.max_drawdown) }}</td>
                <td class="{% if crisis.final_return < 0 %}risk-high{% else %}risk-low{% endif %}">{{ "{:.2%}".format(crisis.final_return) }}</td>
                <td class="{% if crisis.final_return < 0 %}risk-high{% else %}risk-low{% endif %}" style="font-family:monospace;">
                    ${{ "{:,.2f}".format(crisis.final_return * portfolio_value) }}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="section-title">Macro Factor Stress Shock Analysis</div>
    <div style="font-size:12px; margin-bottom: 15px; color:#666;">
        Regresses asset histories on FRED macro series (VIX, 10Y Yield, Oil, USD Index).
        Projected portfolio impact under user-applied shocks:
    </div>
    <table>
        <thead>
            <tr>
                <th>Factor</th>
                <th>Standardized Portfolio Beta</th>
                <th>Applied Shock</th>
                <th>Projected Portfolio Return Impact</th>
                <th>Projected Portfolio Dollar Impact</th>
            </tr>
        </thead>
        <tbody>
            {% for impact in factor_shocks.factor_impacts %}
            <tr>
                <td><strong>{{ impact.factor.upper() }}</strong></td>
                <td>{{ "{:.4f}".format(impact.beta) }}</td>
                <td>
                    {% if impact.factor == 'y10' %}
                        {{ "{:+.1f}".format(impact.native_shock * 100) }} bps
                    {% else %}
                        {{ "{:+.1f}%".format(impact.native_shock * 100) }}
                    {% endif %}
                </td>
                <td class="{% if impact.projected_return_impact < 0 %}risk-high{% else %}risk-low{% endif %}">
                    {{ "{:.2%}".format(impact.projected_return_impact) }}
                </td>
                <td class="{% if impact.projected_usd_impact < 0 %}risk-high{% else %}risk-low{% endif %}" style="font-family:monospace;">
                    ${{ "{:,.2f}".format(impact.projected_usd_impact) }}
                </td>
            </tr>
            {% endfor %}
            <tr style="background-color: #f7fafc; font-weight: bold; border-top: 2px solid #cbd5e0;">
                <td colspan="3"><strong>Total Portfolio Shock Return / P&amp;L</strong></td>
                <td class="{% if factor_shocks.portfolio_projected_return < 0 %}risk-high{% else %}risk-low{% endif %}">
                    {{ "{:.2%}".format(factor_shocks.portfolio_projected_return) }}
                </td>
                <td class="{% if factor_shocks.portfolio_projected_usd < 0 %}risk-high{% else %}risk-low{% endif %}" style="font-family:monospace;">
                    ${{ "{:,.2f}".format(factor_shocks.portfolio_projected_usd) }}
                </td>
            </tr>
        </tbody>
    </table>

    {% if charts %}
        <div class="section-title" style="page-break-before: always;">Visual Risk Analytics</div>
        {% if charts.pnl_dist %}
            <h3>PnL Simulation &amp; VaR Limits</h3>
            <img class="chart-img" src="{{ charts.pnl_dist }}" alt="PnL Distribution Chart" />
        {% endif %}
        {% if charts.drawdowns %}
            <h3>Historical Crisis Performance</h3>
            <img class="chart-img" src="{{ charts.drawdowns }}" alt="Crisis Drawdown Chart" />
        {% endif %}
    {% endif %}

</body>
</html>
"""

def generate_html_report(data: Dict[str, Any]) -> str:
    """
    Fills the report Jinja2 template with computed data.
    """
    template = jinja2.Template(HTML_TEMPLATE)
    # Inject current date if not provided
    if "date" not in data:
        from datetime import datetime
        data["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    return template.render(**data)

def generate_pdf_report(data: Dict[str, Any], output_path: str) -> bool:
    """
    Generates a PDF from the report data.
    If WeasyPrint is available, outputs a PDF.
    Otherwise, uses xhtml2pdf as a fallback to output a PDF.
    If both fail, writes a static HTML report to output_path + '.html' and returns False.
    """
    html_content = generate_html_report(data)
    
    if WEASYPRINT_AVAILABLE:
        try:
            logger.info(f"Rendering PDF report to {output_path} via WeasyPrint...")
            HTML(string=html_content).write_pdf(output_path)
            return True
        except Exception as e:
            logger.error(f"WeasyPrint failed to render PDF: {str(e)}. Falling back to xhtml2pdf...")
            
    # Fallback to xhtml2pdf (pure Python)
    try:
        logger.info(f"Rendering PDF report to {output_path} via xhtml2pdf...")
        from xhtml2pdf import pisa
        with open(output_path, "w+b") as result_file:
            pisa_status = pisa.CreatePDF(html_content, dest=result_file)
        if not pisa_status.err:
            return True
        else:
            logger.error(f"xhtml2pdf error code: {pisa_status.err}. Falling back to writing HTML report.")
            if os.path.exists(output_path):
                os.remove(output_path)
    except Exception as e:
        logger.error(f"xhtml2pdf failed to render PDF: {str(e)}. Falling back to writing HTML report.")
        if os.path.exists(output_path):
            os.remove(output_path)
            
    # Fallback to HTML
    html_fallback_path = output_path
    if not html_fallback_path.endswith(".html"):
        html_fallback_path += ".html"
    
    logger.info(f"Writing fallback HTML report to {html_fallback_path}...")
    try:
        with open(html_fallback_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return False
    except Exception as e:
        logger.error(f"Failed to write fallback HTML report: {str(e)}")
        raise e
