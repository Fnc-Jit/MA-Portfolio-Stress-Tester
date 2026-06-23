# Multi-Asset Portfolio Stress Tester & Scenario Engine
### Full Implementation Plan — Colab → GitHub → Vercel

**Build window:** June 24 – July 1, 2026 (Days 1-6 of your 8-day sprint)
**Target:** GS Risk Technology relevance, recruiter-demoable, production-feel

---

## 1. Project Overview

You're building a tool that does what a bank's market-risk desk does every morning: take a portfolio, hit it with historical crises and hypothetical shocks, and report back how much money it could lose, in how many ways, with how much confidence.

Concretely: a user enters tickers + weights. The engine runs four independent risk-measurement methods (historical replay, parametric VaR, Monte Carlo VaR, factor-shock) against that portfolio, cross-checks them against each other (they should roughly agree — if they don't, that's a modeling insight, not a bug), and renders everything as a one-page risk report plus an interactive dashboard.

The two things that separate this from a typical student "VaR calculator" notebook:
- **Four risk methods cross-validating each other**, not just one. Real risk desks never trust a single VaR number — they triangulate.
- **A working, navigable web app**, not just a notebook. A recruiter clicking a live link and typing in their own portfolio is a fundamentally different impression than scrolling a `.ipynb`.

## 2. Real-World Finance Use Case

Every systemically important bank is required under regulatory frameworks (CCAR/DFAST in the US, similar regimes elsewhere) to stress-test its trading book and balance sheet against defined adverse scenarios, and to report VaR/CVaR daily to risk committees. Asset managers run parallel internal versions for fiduciary risk oversight, even without the regulatory mandate.

GS Risk Technology specifically builds and maintains the *systems* that compute these numbers at scale — not the policy, the pipeline. That's exactly the layer this project lives at: ingestion → computation → reporting, the same shape as production risk infrastructure, just single-portfolio scale instead of firm-wide.

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js, Vercel)                │
│  Landing Page → Portfolio Input Form → Dashboard (4 panels)  │
└───────────────────────────┬───────────────────────────────────┘
                            │ REST calls
┌───────────────────────────▼───────────────────────────────────┐
│              BACKEND API (FastAPI, deployed on Render/Railway) │
│  /portfolio/validate   /risk/compute   /risk/report (PDF)      │
└───────────────────────────┬───────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐  ┌─────────────────┐  ┌──────────────────┐
│ DATA LAYER     │  │ RISK ENGINE      │  │ REPORT GENERATOR │
│ yfinance       │  │ - Historical     │  │ - Chart bundling │
│ FRED (fredapi) │  │ - Parametric VaR │  │ - HTML→PDF       │
│ Local cache     │  │ - Monte Carlo    │  │   (WeasyPrint)   │
│ (Parquet files) │  │ - Factor shock   │  │                  │
└───────────────┘  └─────────────────┘  └──────────────────┘
```

**Why this split:** Colab is where you *develop and validate* the risk engine (fast iteration, no deployment friction). Once the math is correct, the risk engine code gets lifted into a FastAPI service (a thin wrapper — same functions, just exposed as endpoints) which the Vercel frontend calls. This mirrors how real quant research → production pipelines work: research happens in notebooks, production code is the same logic in a service.

You do **not** need to rebuild the risk engine in JavaScript. Keep all math in Python, served via FastAPI. Vercel hosts only the frontend.

## 4. Required APIs and Data Sources

| Source | What you pull | Notes |
|---|---|---|
| **Yahoo Finance** (`yfinance`) | Daily OHLCV for portfolio tickers, 2005-present | Free, no key needed, primary price source |
| **FRED** (`fredapi`, free API key) | 10Y yield (`DGS10`), VIX (`VIXCLS`), WTI oil (`DCOILWTICO`), USD index (`DTWEXBGS`) | Free key from fred.stlouisfed.org/docs/api/api_key.html — takes 2 minutes |

You do not need Financial Modeling Prep, Alpha Vantage, or Polygon for this specific project — `yfinance` + FRED covers everything needed for price history and macro factors. Keep those for later projects (M&A Rater needs FMP/EDGAR, Event Pipeline needs FMP).

## 5. Required Python Libraries

```python
# Core
pandas
numpy
scipy            # scipy.stats, scipy.linalg.cholesky

# Data
yfinance
fredapi

# Visualization
matplotlib
seaborn
plotly           # for the interactive dashboard charts

# Backend (Phase 2, when lifting to FastAPI)
fastapi
uvicorn
pydantic

# Report generation
weasyprint        # HTML -> PDF
jinja2            # HTML templating for the report

# Testing
pytest
```

## 6. Folder/File Structure

Even though Phase 1 is built in Colab, structure it like this from day one — copy cells into these files as you go, so Day 6's "lift to FastAPI" step is just moving files, not rewriting code.

```
portfolio-stress-tester/
├── README.md
├── requirements.txt
├── .gitignore
├── notebooks/
│   └── 01_research_and_validation.ipynb      # your Colab dev notebook
├── risk_engine/
│   ├── __init__.py
│   ├── data_loader.py          # yfinance + FRED pulls, caching
│   ├── historical_replay.py    # crisis scenario replay
│   ├── parametric_var.py       # analytical VaR/CVaR
│   ├── monte_carlo_var.py      # Cholesky-simulated VaR/CVaR
│   ├── factor_shock.py         # macro factor beta + shock impact
│   ├── metrics.py              # Sharpe, max drawdown, vol helpers
│   └── report.py               # PDF/HTML report generation
├── api/
│   ├── main.py                  # FastAPI app
│   ├── schemas.py               # Pydantic request/response models
│   └── routes/
│       ├── portfolio.py
│       └── risk.py
├── frontend/                    # Next.js app, deployed to Vercel
│   ├── app/
│   │   ├── page.tsx             # landing page
│   │   ├── dashboard/page.tsx
│   │   └── api/proxy/route.ts   # optional proxy to FastAPI backend
│   ├── components/
│   │   ├── PortfolioForm.tsx
│   │   ├── RiskSummaryCards.tsx
│   │   ├── PnLDistributionChart.tsx
│   │   ├── DrawdownChart.tsx
│   │   ├── FactorTornadoChart.tsx
│   │   └── CorrelationHeatmap.tsx
│   └── package.json
├── tests/
│   ├── test_parametric_var.py
│   ├── test_monte_carlo_var.py
│   └── test_historical_replay.py
└── data_cache/
    └── *.parquet                # cached price/macro pulls, gitignored
```

## 7. Step-by-Step Build Guide

Mapped to your Day 1–6 sprint:

**Day 1 — Data layer.** Build `data_loader.py`: functions to pull and cache (as local Parquet, to avoid re-hitting `yfinance` every run) price history for any ticker list across the 4 crisis windows, plus the FRED macro series. Build the portfolio input validation (tickers exist, weights sum to 1, no duplicate tickers).

**Day 2 — Historical replay + parametric VaR.** `historical_replay.py` applies each crisis period's actual realized returns to current weights. `parametric_var.py` computes the covariance matrix and analytical VaR/CVaR at 95%/99%, 1-day and 10-day horizons.

**Day 3 — Monte Carlo VaR.** `monte_carlo_var.py`: Cholesky-decompose the covariance matrix, simulate 10,000 correlated return paths (normal and Student-t variants), compute simulated VaR/CVaR, compare to Day 2's parametric numbers.

**Day 4 — Factor shock.** `factor_shock.py`: regress each holding's returns on the 4 FRED macro factors to get factor betas, then let the user define a hypothetical shock vector (e.g., rates +200bps, oil +50%) and project portfolio impact.

**Day 5 — Visualization + report.** Build all Plotly chart functions (these get reused by both the PDF report and the dashboard frontend — write them once, render twice). Build `report.py`: Jinja2 HTML template styled like a bank risk memo, rendered to PDF via WeasyPrint.

**Day 6 — Lift to FastAPI + deploy.** Wrap `risk_engine/` functions in FastAPI routes. Deploy FastAPI to Render or Railway (free tier). Scaffold the Next.js frontend (landing page + dashboard, see sections 11 and 13 below), deploy to Vercel. Wire frontend → backend. Push clean GitHub repo with README.

## 8. Data Collection Pipeline

```python
# risk_engine/data_loader.py — core shape

import yfinance as yf
import pandas as pd
from pathlib import Path
from fredapi import Fred

CACHE_DIR = Path("data_cache")
CACHE_DIR.mkdir(exist_ok=True)

CRISIS_WINDOWS = {
    "gfc_2008":      ("2008-09-01", "2009-03-31"),
    "covid_2020":    ("2020-02-01", "2020-04-30"),
    "taper_2013":    ("2013-05-01", "2013-09-30"),
    "hike_2022":     ("2022-01-01", "2022-10-31"),
}

def fetch_prices(tickers: list[str], start: str = "2005-01-01", end: str | None = None) -> pd.DataFrame:
    """Pull daily adjusted close for all tickers, cache to parquet, return wide DataFrame."""
    cache_key = "_".join(sorted(tickers)) + f"_{start}_{end}.parquet"
    cache_path = CACHE_DIR / cache_key
    if cache_path.exists():
        return pd.read_parquet(cache_path)
    data = yf.download(tickers, start=start, end=end, progress=False)["Close"]
    if isinstance(data, pd.Series):
        data = data.to_frame(name=tickers[0])
    data.to_parquet(cache_path)
    return data

def fetch_macro_factors(fred_api_key: str, start: str = "2005-01-01") -> pd.DataFrame:
    """Pull VIX, 10Y yield, oil, USD index from FRED."""
    fred = Fred(api_key=fred_api_key)
    series = {
        "vix":   "VIXCLS",
        "y10":   "DGS10",
        "oil":   "DCOILWTICO",
        "usd":   "DTWEXBGS",
    }
    df = pd.DataFrame({name: fred.get_series(code, start) for name, code in series.items()})
    return df.dropna()

def get_crisis_window_returns(tickers: list[str], crisis_name: str) -> pd.DataFrame:
    """Return daily returns for tickers during a named historical crisis window."""
    start, end = CRISIS_WINDOWS[crisis_name]
    prices = fetch_prices(tickers, start=start, end=end)
    return prices.pct_change().dropna()
```

**Validation checks to build in alongside this (don't skip):**
- Confirm every requested ticker actually returned data (yfinance silently drops delisted/typo'd tickers — catch this explicitly and surface it to the user rather than letting weights silently renormalize over fewer assets than expected).
- Confirm crisis-window data isn't empty (some tickers IPO'd after 2008 — handle gracefully: exclude that ticker from that specific crisis replay and flag it in the report, don't crash).

## 9. Data Cleaning & Feature Engineering

- **Missing data:** forward-fill up to 2 consecutive missing days (holidays/data gaps), drop tickers with >5% missing data in the lookback window, flag this in the output report rather than silently proceeding.
- **Returns:** use log returns (`np.log(p_t / p_{t-1})`) for the covariance matrix and VaR math — they're additive across time and better-behaved for the Cholesky step; use simple returns only for the final P&L dollar-impact translation.
- **Covariance matrix:** use a lookback window of 2 years of daily returns by default (configurable). For Day 3's Monte Carlo step, check the covariance matrix is positive semi-definite before attempting Cholesky decomposition (it can fail to be PD with too few observations relative to number of assets — if it does, apply a small ridge adjustment, document why in code comments).
- **Factor betas (Day 4):** standardize macro factor series (z-score) before regression so beta magnitudes are comparable across factors with very different native units (oil in dollars, VIX in points, rates in percent).

## 10. Core Models/Algorithms

**Parametric VaR/CVaR:**
```
σ_portfolio = sqrt(w^T Σ w)
VaR_95,1day = z_0.95 * σ_portfolio * portfolio_value
CVaR_95 = σ_portfolio * portfolio_value * φ(z_0.95) / (1 - 0.95)
```
where `w` = weight vector, `Σ` = covariance matrix, `z` = normal quantile, `φ` = normal PDF.

**Monte Carlo VaR:**
```
L = cholesky(Σ)
simulated_returns = mean_vector + L @ random_normal(n_assets, n_sims)
portfolio_pnl_sims = simulated_returns.T @ w * portfolio_value
VaR_95 = -percentile(portfolio_pnl_sims, 5)
CVaR_95 = -mean(portfolio_pnl_sims[portfolio_pnl_sims <= -VaR_95])
```
Run twice: once with `np.random.multivariate_normal`, once substituting Student-t draws (df=5) scaled by the same covariance, to show fat-tail sensitivity.

**Historical replay:** straightforward — apply each crisis window's day-by-day realized return path to current weights, compound to get cumulative portfolio P&L over that window, report max drawdown within it.

**Factor shock:** OLS regression of each asset's returns on the 4 standardized macro factors gives a beta vector per asset; portfolio factor exposure = weighted sum of betas; shock impact = exposure vector dotted with user-defined shock vector.

## 11. Visualizations & Dashboard Components

Build each as a standalone Plotly function in `risk_engine/`, reused in both the PDF report and the frontend (frontend can either re-render Plotly JSON via `react-plotly.js`, or call the FastAPI backend for pre-rendered chart images — pick whichever is faster for you, JSON re-render is more interactive).

1. **P&L Distribution Histogram** — Monte Carlo simulated P&L distribution, with parametric VaR/CVaR and historical VaR lines overlaid as vertical markers, so all three methods are visually compared on one chart.
2. **Crisis Drawdown Curves** — line chart, one line per historical crisis (GFC/COVID/Taper/2022), showing cumulative portfolio P&L through each window, normalized to start at 0.
3. **Factor Sensitivity Tornado Chart** — horizontal bar chart showing portfolio $ impact per factor under the user's defined shock vector, sorted by magnitude.
4. **Correlation Heatmap** — portfolio constituent correlation matrix, annotated.
5. **Risk Summary Cards** (not a chart — a UI component): 4-6 number cards up top — 1-day 95% VaR, 1-day 99% VaR, CVaR 95%, worst historical crisis P&L, current portfolio volatility (annualized).

## 12. Performance Metrics

Report these for every method, side by side in a comparison table:
- VaR (95%, 99%) — 1-day and 10-day horizon
- CVaR / Expected Shortfall (95%, 99%)
- Max drawdown (per crisis scenario)
- Annualized volatility
- Sharpe ratio (using risk-free rate from FRED's 3-month T-bill series)
- Method agreement check: % difference between parametric and Monte Carlo VaR — large divergence signals fat tails or non-normality the parametric method is missing, and you should say this explicitly in the report.

## 13. Final Deliverables

- **Working Colab notebook** (`01_research_and_validation.ipynb`) — your dev/validation environment, kept in the repo as proof of research process.
- **Clean Python package** (`risk_engine/`) with docstrings, type hints, and a `tests/` suite covering at minimum: VaR calculation correctness on a known synthetic 2-asset portfolio (where you can hand-calculate the expected answer), Cholesky decomposition validity check, and historical replay date-range correctness.
- **FastAPI backend**, deployed and publicly reachable (Render/Railway free tier).
- **Next.js frontend**, deployed on Vercel, with a live portfolio-input form and full dashboard.
- **Auto-generated PDF risk report** — downloadable from the dashboard, styled like an actual bank risk memo.
- **GitHub repo** with a README that includes: methodology explanation, architecture diagram (the one in section 3), screenshots, live demo link, and an honest "Limitations" section (e.g., "parametric VaR assumes normal returns; Monte Carlo with Student-t partially addresses this; see Day 3 comparison").

## 14. Resume Description

> **Multi-Asset Portfolio Stress Tester & Scenario Engine** | Python, FastAPI, Next.js, Plotly
> Built a full-stack risk engine computing VaR/CVaR across four independent methodologies (historical replay, parametric, Monte Carlo with Cholesky-decomposed correlated shocks, macro factor-shock) for arbitrary user-defined portfolios; deployed live on Vercel with FastAPI backend, auto-generated PDF risk reporting, and cross-method validation surfacing model divergence under fat-tailed conditions.

---

## Dashboard Section Spec (hand this directly to a frontend AI builder)

**Page: `/dashboard`**

Layout: single-page, top-to-bottom scroll, 4 sections.

1. **Header bar:** portfolio name/ticker list summary, "Re-run" button, "Download PDF Report" button.
2. **Risk Summary Cards row:** 5 cards horizontally (responsive grid, stack on mobile) — 1-day 95% VaR, 1-day 99% VaR, CVaR 95%, Worst Historical Crisis P&L (with crisis name labeled), Annualized Volatility. Each card: large number, small label below, color-coded (red shades for VaR magnitude scaling).
3. **Charts grid (2x2 on desktop, stacked on mobile):** P&L Distribution Histogram (top-left), Crisis Drawdown Curves (top-right), Factor Sensitivity Tornado (bottom-left), Correlation Heatmap (bottom-right). Each chart in a card with a title and a one-line method explanation caption beneath it.
4. **Method Comparison Table:** rows = VaR/CVaR/Sharpe/Vol, columns = Historical / Parametric / Monte Carlo / Factor-Shock (where applicable), with an "agreement flag" badge if methods diverge by more than a set threshold.

**Visual style:** dark theme, navy/charcoal background, single accent color (amber or teal) for interactive elements and chart highlights — avoid default Bootstrap blue. Monospace font for all numeric values (VaR figures, percentages) to read as "terminal-grade," sans-serif for labels/headers.

## Landing Page Spec (hand this directly to a frontend AI builder)

**Page: `/` (root)**

1. **Hero section:** Tool name ("Portfolio Stress Tester"), one-sentence value prop ("Stress-test any portfolio against historical crises and hypothetical macro shocks — the same risk methodology banks use, in your browser"), a single CTA button → portfolio input form. No stock photos; use a static preview image of the dashboard itself (screenshot) as the hero visual.
2. **"How it works" 3-step strip:** (1) Enter your portfolio → (2) We run 4 independent risk models → (3) Get a full risk report in seconds. Each step with a small icon, no heavy illustration.
3. **Methodology trust section:** 4 small cards naming each method (Historical Replay, Parametric VaR, Monte Carlo Simulation, Factor Shock) with a 1-sentence description each — this section exists specifically to signal rigor to a technically literate visitor (recruiter/interviewer) skimming the page.
4. **Footer:** GitHub repo link, your name, "Built by Jitraj Esh" — keep it understated, not a generic SaaS footer.

**Visual style:** same dark theme as dashboard for continuity. Keep copy terse — no marketing fluff, this page is selling competence, not a SaaS product.
