# Kalman‑Filter Pairs‑Trading: A Backtested Evaluation

A from‑scratch, cost‑aware evaluation of the Kalman‑filter pairs‑trading framework described in
RuujSs's article *"How To Use The Kalman Filter To Build Smarter Trading Systems"*
([@RuujSs](https://x.com/RuujSs/status/2069430225801490602)), benchmarked against the textbook
treatment in Palomar (2025), *Portfolio Optimization*, [Chapter 15.6](https://portfoliooptimizationbook.com/book/15.6-kalman-pairs-trading.html).

## 📄 Read the full evaluation: [`REPORT.md`](REPORT.md)

It walks through RuujSs's idea step by step, then evaluates viability with historical data and backtests.

### Headline findings
- ✅ Kalman gives a **much more stable hedge ratio** and a **more stationary spread** than rolling OLS — reproduced almost exactly from the book.
- ⚠️ The famous "Kalman is a must / 3.2× return" result **depends on ignoring transaction costs**. With realistic costs, basic Kalman ≈ rolling OLS on a risk‑adjusted basis.
- ❌ The book's "best" variant (Kalman + momentum) is the **worst** tradeable strategy after costs (it overtrades a tiny‑variance spread).
- 🎯 Verdict: a sound **estimator upgrade**, not a standalone edge. Viable only as part of a diversified, low‑cost, cointegration‑screened stat‑arb book.

## Project layout

```
src/
  data.py            # yfinance download + caching
  cointegration.py   # Engle-Granger, ADF, OU half-life
  estimators.py      # rolling OLS, Kalman (basic), Kalman + momentum
  backtest.py        # signals, proportional/threshold sizing, costs, metrics
  run_analysis.py    # end-to-end pipeline -> results/ + figures/
  aggregate.py       # aggregated comparison tables
analysis/
  ruujss_article.txt # archived source article
  results/           # CSV/JSON outputs
  figures/           # charts
REPORT.md            # the full write-up
```

## Reproduce

```bash
pip install -r requirements.txt
cd src && python run_analysis.py && python aggregate.py
```

*Research evaluation only — not investment advice.*
