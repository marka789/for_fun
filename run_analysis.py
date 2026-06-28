#!/usr/bin/env python3
"""
Run covariance / PCA / RMT analysis for S&P 500 and Nasdaq-100 since 2020.

Steps (Laloux et al. 1999 style):
  1. Build sample covariance and correlation matrices from daily returns.
  2. PCA eigendecomposition + Marchenko-Pastur random matrix theory diagnostics.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow imports from project root.
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from config import DATA_DIR, NASDAQ100_LABEL, OUTPUT_DIR, SP500_LABEL, START_DATE
from src.analysis import UniverseResult, analyze_universe
from src.constituents import get_nasdaq100_tickers, get_sp500_tickers
from src.data_loader import compute_log_returns, download_prices


def print_result(r: UniverseResult) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {r.label.upper()}")
    print(f"{'=' * 60}")
    print(f"  Assets (N):              {r.n_assets}")
    print(f"  Observations (T):        {r.n_observations}")
    print(f"  q = N/T:                 {r.q_ratio:.4f}")
    print(f"  Fitted σ² (MP):          {r.sigma2:.4f}")
    print(f"  MP bulk:                 [{r.lambda_minus:.4f}, {r.lambda_plus:.4f}]")
    print(f"  Market mode λ₁:          {r.top_eigenvalue:.2f}  ({100*r.top_pc_variance_share:.1f}% var)")
    print(f"  Signal eigenvalues:      {r.n_signal_eigenvalues}  ({100*r.variance_explained_signal:.1f}% var)")
    print(f"  Noise eigenvalues:       {r.n_noise_eigenvalues}")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Equity covariance / PCA / RMT analysis — data from {START_DATE}")
    print(f"Outputs -> {OUTPUT_DIR}\n")

    # --- Fetch constituents ---
    sp500_tickers = get_sp500_tickers()
    ndx_tickers = get_nasdaq100_tickers()
    print(f"S&P 500 constituents:   {len(sp500_tickers)}")
    print(f"Nasdaq-100 constituents: {len(ndx_tickers)}")

    # --- Download prices ---
    sp500_prices = download_prices(sp500_tickers, SP500_LABEL)
    ndx_prices = download_prices(ndx_tickers, NASDAQ100_LABEL)

    sp500_returns = compute_log_returns(sp500_prices)
    ndx_returns = compute_log_returns(ndx_prices)

    # --- Step 1 & 2 ---
    sp500_result = analyze_universe(sp500_returns, SP500_LABEL)
    ndx_result = analyze_universe(ndx_returns, NASDAQ100_LABEL)

    print_result(sp500_result)
    print_result(ndx_result)

    combined = {
        "start_date": START_DATE,
        "universes": {
            SP500_LABEL: sp500_result.__dict__,
            NASDAQ100_LABEL: ndx_result.__dict__,
        },
    }
    summary_path = OUTPUT_DIR / "analysis_summary.json"
    summary_path.write_text(json.dumps(combined, indent=2))
    print(f"\nAll outputs saved to {OUTPUT_DIR}")
    print(f"Summary -> {summary_path}")


if __name__ == "__main__":
    main()
