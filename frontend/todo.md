# Portfolio Stress Tester - Project TODO

## Landing Page
- [x] Hero section with tool name, value proposition, and "Get Started" CTA button
- [x] "How it works" 3-step strip with icons (Enter portfolio → Run 4 models → Get report)
- [x] Methodology trust section with 4 cards (Historical Replay, Parametric VaR, Monte Carlo, Factor Shock)
- [x] Footer with GitHub link and "Built by Jitraj Esh" credit
- [x] Vibrant animated craft elements and visual energy

## Portfolio Input & Navigation
- [x] Portfolio input form (tickers + weights) accessible from landing page CTA
- [x] Form validation and error handling
- [x] Navigation between landing page and dashboard

## Dashboard
- [x] Dashboard header bar (portfolio summary, Re-run button, Download PDF button)
- [x] Risk Summary Cards row (1-day 95% VaR, 1-day 99% VaR, CVaR 95%, Worst Crisis P&L, Annualized Vol)
- [x] Risk Summary Cards styled with red shades and monospace numeric fonts
- [x] Charts grid 2x2 desktop / stacked mobile (P&L Distribution, Crisis Drawdown, Factor Tornado, Correlation Heatmap)
- [x] Each chart with title and method caption
- [x] Method Comparison Table (VaR, CVaR, Sharpe, Vol rows; Historical/Parametric/MC/Factor columns)
- [x] Agreement-flag badge for model divergence in comparison table

## Styling & Theme
- [x] Dark navy/charcoal background theme
- [x] Amber accent color for interactive elements
- [x] Monospace font for all numeric values
- [x] Responsive design (desktop and mobile)
- [x] Finance-grade, data-dense visual aesthetic

## Mock Data & Computation
- [x] Mock risk computation engine (parametric VaR, Monte Carlo, historical, factor shock)
- [x] Portfolio-based mock data generation
- [x] Chart data generation for all 4 chart types

## Testing & Delivery
- [ ] Vitest unit tests for core components
- [ ] Cross-browser and responsive testing
- [ ] Add portfolio form validation (required tickers, numeric weights, total checks)
- [ ] Compute model divergence dynamically and show agreement badge only on divergence
- [ ] Final checkpoint and delivery
