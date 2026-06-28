"""End-to-end evaluation of the Kalman-filter pairs-trading strategy.

Reproduces and stress-tests the central claim from RuujSs's article and
Palomar (2025) Ch. 15.6: that a Kalman-filtered dynamic hedge ratio beats a
rolling-OLS hedge ratio for pairs trading.

Outputs (written under analysis/):
  results/cointegration.csv  - pair diagnostics
  results/metrics.csv        - full backtest grid (pair x method x period x cost)
  results/summary.json       - headline aggregates
  figures/*.png              - hedge ratios, spreads, equity curves, summary
"""

from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from backtest import (
    backtest_spread,
    proportional_position,
    signal_from_z,
    spread_quality,
    zscore,
)
from cointegration import summarize_pair
from data import aligned_pair, get_prices
from estimators import kalman_basic, kalman_momentum, rolling_ols

HERE = os.path.dirname(__file__)
ANALYSIS = os.path.join(HERE, "..", "analysis")
RESULTS = os.path.join(ANALYSIS, "results")
FIGURES = os.path.join(ANALYSIS, "figures")

# Pairs: book references first, then additional economically-motivated pairs,
# plus a deliberate "junk" pair to expose false positives.
PAIRS = [
    ("EWA", "EWC", "Australia vs Canada ETFs (book)"),
    ("KO", "PEP", "Coca-Cola vs Pepsi (book)"),
    ("GLD", "GDX", "Gold vs gold miners"),
    ("V", "MA", "Visa vs Mastercard"),
    ("XOM", "CVX", "Exxon vs Chevron"),
    ("HD", "LOW", "Home Depot vs Lowe's"),
    ("GS", "MS", "Goldman vs Morgan Stanley"),
    ("AAPL", "XOM", "Apple vs Exxon (junk/control)"),
]

FETCH_START = "2011-01-01"
FETCH_END = "2025-06-01"
PERIODS = {
    "book_era_2013_2022": ("2013-01-01", "2022-12-31"),
    "oos_2023_2025": ("2023-01-01", "2025-06-01"),
    "full_2013_2025": ("2013-01-01", "2025-06-01"),
}
TC_LEVELS = {"no_cost": 0.0, "tc_5bps": 5.0, "tc_10bps": 10.0}

ENTRY = 1.0
EXIT = 0.0
Z_LOOKBACK = 126  # ~6 months, matching the book


def all_tickers():
    s = set()
    for a, b, _ in PAIRS:
        s.add(a)
        s.add(b)
    return sorted(s)


def build_estimators(y1, y2):
    return {
        "rolling_ols": rolling_ols(y1, y2, lookback=504),
        "kalman_basic": kalman_basic(y1, y2, alpha=1e-5),
        "kalman_momentum": kalman_momentum(y1, y2, alpha=1e-6),
    }


def slice_period(series, start, end):
    return series.loc[(series.index >= pd.Timestamp(start)) & (series.index <= pd.Timestamp(end))]


def run():
    os.makedirs(RESULTS, exist_ok=True)
    os.makedirs(FIGURES, exist_ok=True)

    prices = get_prices(all_tickers(), start=FETCH_START, end=FETCH_END)
    prices.to_csv(os.path.join(RESULTS, "prices.csv"))

    coint_rows = []
    metric_rows = []
    quality_rows = []
    estimator_cache = {}

    for a, b, desc in PAIRS:
        pair = aligned_pair(prices, a, b)
        if pair.shape[0] < 500:
            print(f"skip {a}-{b}: insufficient data")
            continue
        y1, y2 = pair[a], pair[b]

        # Cointegration diagnostics on the book era (in-sample qualification).
        is_y1 = slice_period(y1, "2013-01-01", "2022-12-31")
        is_y2 = slice_period(y2, "2013-01-01", "2022-12-31")
        diag = summarize_pair(is_y1, is_y2)
        diag.update({"pair": f"{a}-{b}", "desc": desc})
        coint_rows.append(diag)

        est = build_estimators(y1, y2)
        estimator_cache[(a, b)] = (y1, y2, est)

        # --- Spread quality (book era, on the normalized spread) -----------
        for method, edf in est.items():
            ns_is = slice_period(edf["norm_spread"], "2013-01-01", "2022-12-31")
            g_is = slice_period(edf["gamma"], "2013-01-01", "2022-12-31").dropna()
            q = spread_quality(ns_is)
            q.update({
                "pair": f"{a}-{b}", "method": method,
                "gamma_vol": float(g_is.diff().std()),
                "gamma_min": float(g_is.min()), "gamma_max": float(g_is.max()),
            })
            quality_rows.append(q)

        # --- Trading grid --------------------------------------------------
        # signal base = normalized spread (book convention).
        for method, edf in est.items():
            z = zscore(edf["norm_spread"], Z_LOOKBACK)
            signals = {
                "threshold_z": signal_from_z(z, entry=ENTRY, exit=EXIT),
                "proportional": proportional_position(z, cap=2.0),
            }
            # Kalman-native innovation z (article's specific recommendation).
            if "kalman_z" in edf:
                signals["kalman_z"] = signal_from_z(edf["kalman_z"], entry=ENTRY, exit=EXIT)

            for signame, sig in signals.items():
                for pname, (pstart, pend) in PERIODS.items():
                    y1p = slice_period(y1, pstart, pend)
                    y2p = slice_period(y2, pstart, pend)
                    gp = slice_period(edf["gamma"], pstart, pend)
                    sp = slice_period(sig, pstart, pend)
                    for cname, tc in TC_LEVELS.items():
                        res = backtest_spread(y1p, y2p, gp, sp, tc_bps=tc)
                        if res is None:
                            continue
                        row = {
                            "pair": f"{a}-{b}",
                            "method": method,
                            "signal": signame,
                            "period": pname,
                            "cost": cname,
                        }
                        row.update(res["stats"])
                        metric_rows.append(row)

    coint_df = pd.DataFrame(coint_rows)
    coint_df.to_csv(os.path.join(RESULTS, "cointegration.csv"), index=False)
    metrics_df = pd.DataFrame(metric_rows)
    metrics_df.to_csv(os.path.join(RESULTS, "metrics.csv"), index=False)
    quality_df = pd.DataFrame(quality_rows)
    quality_df.to_csv(os.path.join(RESULTS, "spread_quality.csv"), index=False)

    make_figures(estimator_cache)
    make_summary_charts(metrics_df, quality_df)
    make_summary(metrics_df, coint_df)
    print("DONE. wrote results to", RESULTS)
    return metrics_df, coint_df


def make_figures(cache):
    # Detailed diagnostic figures for the two book pairs.
    for a, b in [("EWA", "EWC"), ("KO", "PEP")]:
        if (a, b) not in cache:
            continue
        y1, y2, est = cache[(a, b)]
        mask = (y1.index >= pd.Timestamp("2013-01-01")) & (y1.index <= pd.Timestamp("2025-06-01"))

        # Hedge ratio tracking
        fig, ax = plt.subplots(figsize=(11, 4))
        for m, c in [("rolling_ols", "tab:red"), ("kalman_basic", "tab:blue"),
                     ("kalman_momentum", "tab:green")]:
            ax.plot(est[m]["gamma"][mask].index, est[m]["gamma"][mask].values,
                    label=m, color=c, lw=1.1)
        ax.set_title(f"Hedge ratio tracking: {a}-{b}")
        ax.set_ylabel("gamma (hedge ratio)")
        ax.legend()
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(os.path.join(FIGURES, f"hedge_ratio_{a}_{b}.png"), dpi=120)
        plt.close(fig)

        # Spread comparison
        fig, ax = plt.subplots(figsize=(11, 4))
        for m, c in [("rolling_ols", "tab:red"), ("kalman_basic", "tab:blue"),
                     ("kalman_momentum", "tab:green")]:
            ax.plot(est[m]["spread"][mask].index, est[m]["spread"][mask].values,
                    label=m, color=c, lw=0.8, alpha=0.8)
        ax.set_title(f"Spread (residual) comparison: {a}-{b}")
        ax.set_ylabel("spread")
        ax.legend()
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(os.path.join(FIGURES, f"spread_{a}_{b}.png"), dpi=120)
        plt.close(fig)

        # Equity curves: threshold signal, no-cost vs net-5bps, full 2013-2025
        for sizing in ["threshold", "proportional"]:
            fig, ax = plt.subplots(figsize=(11, 4.5))
            for m, c in [("rolling_ols", "tab:red"), ("kalman_basic", "tab:blue"),
                         ("kalman_momentum", "tab:green")]:
                edf = est[m]
                z = zscore(edf["norm_spread"], Z_LOOKBACK)
                if sizing == "threshold":
                    sig = signal_from_z(z, entry=ENTRY, exit=EXIT)
                else:
                    sig = proportional_position(z, cap=2.0)
                y1p = slice_period(y1, "2013-01-01", "2025-06-01")
                y2p = slice_period(y2, "2013-01-01", "2025-06-01")
                gp = slice_period(edf["gamma"], "2013-01-01", "2025-06-01")
                sp = slice_period(sig, "2013-01-01", "2025-06-01")
                res = backtest_spread(y1p, y2p, gp, sp, tc_bps=5.0)
                if res is not None:
                    ax.plot(res["equity"].index, res["equity"].values,
                            label=f"{m} (net 5bps)", color=c, lw=1.3)
                    ax.plot(res["gross_equity"].index, res["gross_equity"].values,
                            color=c, lw=0.9, ls=":", alpha=0.7)
            ax.axhline(1.0, color="k", lw=0.6, ls="--")
            ax.set_title(f"Cumulative equity ({sizing} sizing): {a}-{b}  "
                         f"[solid=net 5bps, dotted=gross]")
            ax.set_ylabel("growth of $1")
            ax.legend(fontsize=8)
            ax.grid(alpha=0.3)
            fig.tight_layout()
            fig.savefig(os.path.join(FIGURES, f"equity_{sizing}_{a}_{b}.png"), dpi=120)
            plt.close(fig)


REAL_PAIRS = ["EWA-EWC", "KO-PEP", "GLD-GDX", "V-MA", "XOM-CVX", "HD-LOW", "GS-MS"]


def make_summary_charts(metrics_df, quality_df):
    methods = ["rolling_ols", "kalman_basic", "kalman_momentum"]
    colors = {"rolling_ols": "tab:red", "kalman_basic": "tab:blue",
              "kalman_momentum": "tab:green"}
    real = metrics_df[metrics_df["pair"].isin(REAL_PAIRS)]

    # (1) Mean Sharpe by method & cost level (threshold signal, full period).
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for ax, signame, title in [
        (axes[0], "threshold_z", "Threshold signal"),
        (axes[1], "proportional", "Proportional sizing (book-style)"),
    ]:
        costs = ["no_cost", "tc_5bps", "tc_10bps"]
        x = np.arange(len(costs))
        w = 0.25
        for i, m in enumerate(methods):
            vals = [real[(real.signal == signame) & (real.period == "full_2013_2025")
                         & (real.cost == c) & (real.method == m)]["sharpe"].mean()
                    for c in costs]
            ax.bar(x + (i - 1) * w, vals, w, label=m, color=colors[m])
        ax.set_xticks(x)
        ax.set_xticklabels(costs)
        ax.axhline(0, color="k", lw=0.6)
        ax.set_title(f"{title}\nmean Sharpe over 7 pairs, 2013-2025")
        ax.set_ylabel("mean Sharpe")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, "summary_sharpe_by_cost.png"), dpi=120)
    plt.close(fig)

    # (2) Spread quality: ADF stat and hedge-ratio volatility by method.
    q = quality_df[quality_df["pair"].isin(REAL_PAIRS)]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    pairs = REAL_PAIRS
    x = np.arange(len(pairs))
    w = 0.25
    for i, m in enumerate(methods):
        adf = [q[(q.pair == p) & (q.method == m)]["adf_stat"].values[0] for p in pairs]
        axes[0].bar(x + (i - 1) * w, adf, w, label=m, color=colors[m])
    axes[0].axhline(-2.86, color="k", ls="--", lw=0.8, label="5% ADF crit (-2.86)")
    axes[0].set_xticks(x); axes[0].set_xticklabels(pairs, rotation=45, ha="right", fontsize=8)
    axes[0].set_title("Spread stationarity (ADF stat, more negative = better)")
    axes[0].legend(fontsize=7)
    axes[0].grid(alpha=0.3, axis="y")
    for i, m in enumerate(methods):
        gv = [q[(q.pair == p) & (q.method == m)]["gamma_vol"].values[0] for p in pairs]
        axes[1].bar(x + (i - 1) * w, gv, w, label=m, color=colors[m])
    axes[1].set_xticks(x); axes[1].set_xticklabels(pairs, rotation=45, ha="right", fontsize=8)
    axes[1].set_title("Hedge-ratio day-to-day volatility (lower = more stable)")
    axes[1].legend(fontsize=7)
    axes[1].grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, "summary_spread_quality.png"), dpi=120)
    plt.close(fig)


def make_summary(metrics_df, coint_df):
    if metrics_df.empty:
        return
    summary = {}
    # Average Sharpe by method on full period net of 5bps, rolling-z signal.
    for signame in ["threshold_z", "proportional"]:
        sel = metrics_df[(metrics_df["period"] == "full_2013_2025")
                         & (metrics_df["cost"] == "tc_5bps")
                         & (metrics_df["signal"] == signame)]
        summary[f"avg_sharpe_by_method_{signame}_5bps"] = (
            sel.groupby("method")["sharpe"].mean().round(3).to_dict()
        )
        summary[f"median_sharpe_by_method_{signame}_5bps"] = (
            sel.groupby("method")["sharpe"].median().round(3).to_dict()
        )
    # Book pairs detail (threshold signal, full period)
    for pair in ["EWA-EWC", "KO-PEP"]:
        p = metrics_df[(metrics_df["pair"] == pair)
                       & (metrics_df["period"] == "full_2013_2025")
                       & (metrics_df["signal"] == "threshold_z")]
        summary[pair] = (
            p.pivot_table(index="method", columns="cost", values="sharpe").round(3)
            .to_dict()
        )
    with open(os.path.join(RESULTS, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    run()
