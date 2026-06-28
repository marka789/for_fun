"""Aggregate the backtest grid into the tables used in the written report."""

import os

import pandas as pd

HERE = os.path.dirname(__file__)
RESULTS = os.path.join(HERE, "..", "analysis", "results")

REAL_PAIRS = ["EWA-EWC", "KO-PEP", "GLD-GDX", "V-MA", "XOM-CVX", "HD-LOW", "GS-MS"]
JUNK = "AAPL-XOM"


def main():
    m = pd.read_csv(os.path.join(RESULTS, "metrics.csv"))
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)
    pd.set_option("display.float_format", lambda x: f"{x:0.3f}")

    out_lines = []

    def show(title, df):
        out_lines.append(f"\n### {title}\n")
        out_lines.append(df.to_string())
        print(title)
        print(df.to_string())
        print()

    real = m[m.pair.isin(REAL_PAIRS)]

    # 1) Method comparison, threshold signal, full period, by cost level
    for cost in ["no_cost", "tc_5bps", "tc_10bps"]:
        sel = real[(real.signal == "threshold_z") & (real.period == "full_2013_2025")
                   & (real.cost == cost)]
        agg = sel.groupby("method").agg(
            mean_sharpe=("sharpe", "mean"),
            median_sharpe=("sharpe", "median"),
            mean_ann_ret=("ann_return", "mean"),
            mean_maxdd=("max_drawdown", "mean"),
            mean_trades=("n_trades", "mean"),
            mean_turnover=("avg_turnover", "mean"),
        ).round(3)
        show(f"Threshold signal | full 2013-2025 | {cost} | avg over 7 real pairs", agg)

    # 2) Out-of-sample 2023-2025, threshold, 5bps
    sel = real[(real.signal == "threshold_z") & (real.period == "oos_2023_2025")
               & (real.cost == "tc_5bps")]
    agg = sel.groupby("method").agg(
        mean_sharpe=("sharpe", "mean"),
        median_sharpe=("sharpe", "median"),
        mean_ann_ret=("ann_return", "mean"),
        mean_maxdd=("max_drawdown", "mean"),
    ).round(3)
    show("Threshold signal | OOS 2023-2025 | tc_5bps | avg over 7 real pairs", agg)

    # 3) Proportional sizing (book-style), full period, no_cost vs 5bps
    for cost in ["no_cost", "tc_5bps"]:
        sel = real[(real.signal == "proportional") & (real.period == "full_2013_2025")
                   & (real.cost == cost)]
        agg = sel.groupby("method").agg(
            mean_sharpe=("sharpe", "mean"),
            mean_ann_ret=("ann_return", "mean"),
            mean_total_ret=("total_return", "mean"),
            mean_maxdd=("max_drawdown", "mean"),
        ).round(3)
        show(f"Proportional sizing | full 2013-2025 | {cost} | avg over 7 real pairs", agg)

    # 4) Per-pair Sharpe matrix, threshold, full, 5bps
    sel = real[(real.signal == "threshold_z") & (real.period == "full_2013_2025")
               & (real.cost == "tc_5bps")]
    piv = sel.pivot_table(index="pair", columns="method", values="sharpe").round(2)
    show("Per-pair Sharpe | threshold | full 2013-2025 | tc_5bps", piv)

    # 5) Junk pair check
    junk = m[(m.pair == JUNK) & (m.signal == "threshold_z")
             & (m.period == "full_2013_2025") & (m.cost == "tc_5bps")]
    show("JUNK pair AAPL-XOM | threshold | full | tc_5bps",
         junk[["method", "sharpe", "ann_return", "max_drawdown", "n_trades"]].round(3))

    with open(os.path.join(RESULTS, "aggregate_tables.md"), "w") as f:
        f.write("# Aggregated backtest tables\n")
        f.write("\n".join(out_lines))


if __name__ == "__main__":
    main()
