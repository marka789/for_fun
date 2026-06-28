"""Event-style vectorised backtest for a single pairs-trading spread.

Conventions that keep the test honest:

* Signals are formed from the *predicted* hedge ratio gamma_{t|t-1} and the
  spread known at the close of day t.
* Positions are shifted by one day (next-day execution) so we never trade on
  information we could not have had.
* Returns are gross-exposure normalised: we hold 1 share of the long leg and
  gamma shares (in absolute value) of the short leg, and divide daily P&L by
  the gross dollar exposure so the series is a clean per-unit-capital return.
* Transaction costs are charged on the dollar turnover of both legs whenever
  the target position or the hedge ratio changes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def zscore(series: pd.Series, lookback: int = 126) -> pd.Series:
    """Rolling z-score (causal: uses trailing window only)."""
    mean = series.rolling(lookback).mean()
    std = series.rolling(lookback).std()
    return (series - mean) / std


def signal_from_z(z: pd.Series, entry: float = 1.0, exit: float = 0.0) -> pd.Series:
    """Threshold mean-reversion signal in {-1, 0, +1} on the spread.

    Enter long-spread when z <= -entry, short-spread when z >= +entry, and
    flatten when z crosses back through ``exit`` toward zero. Position is held
    (state machine) between entry and exit.
    """
    pos = np.zeros(len(z))
    state = 0
    zv = z.values
    for i in range(len(zv)):
        zi = zv[i]
        if np.isnan(zi):
            pos[i] = 0
            state = 0
            continue
        if state == 0:
            if zi >= entry:
                state = -1
            elif zi <= -entry:
                state = 1
        elif state == 1:  # long spread, wait for revert up to -exit
            if zi >= -exit:
                state = 0
        elif state == -1:  # short spread, wait for revert down to +exit
            if zi <= exit:
                state = 0
        pos[i] = state
    return pd.Series(pos, index=z.index)


def proportional_position(z: pd.Series, cap: float = 2.0) -> pd.Series:
    """Linear (proportional) policy: hold -z units of the spread, capped.

    This is the smooth, always-on policy that produces the book's compounding
    cumulative-return curves. Position grows linearly with the deviation.
    """
    pos = (-z).clip(-cap, cap) / cap
    return pos.fillna(0)


def spread_quality(spread: pd.Series) -> dict:
    """Stationarity / smoothness diagnostics for a spread series.

    Captures *where the Kalman filter genuinely wins*: a more stationary,
    lower-variance, faster-mean-reverting spread.
    """
    from statsmodels.tsa.stattools import adfuller

    s = spread.dropna()
    if len(s) < 60:
        return {"adf_stat": np.nan, "adf_pvalue": np.nan, "half_life": np.nan,
                "std": np.nan}
    adf_stat, adf_p = adfuller(s, maxlag=1, regression="c", autolag="AIC")[:2]
    lag = s.shift(1).dropna()
    delta = (s - s.shift(1)).dropna()
    lag = lag.loc[delta.index]
    x = np.vstack([np.ones(len(lag)), lag.values]).T
    beta = np.linalg.lstsq(x, delta.values, rcond=None)[0][1]
    hl = float("inf") if beta >= 0 else float(-np.log(2) / beta)
    return {"adf_stat": float(adf_stat), "adf_pvalue": float(adf_p),
            "half_life": hl, "std": float(s.std())}


def backtest_spread(y1: pd.Series, y2: pd.Series, gamma: pd.Series,
                    signal: pd.Series, tc_bps: float = 5.0) -> dict:
    """Run the backtest and return a results dict with the equity curve & stats.

    tc_bps: one-way transaction cost in basis points applied to leg turnover.
    """
    df = pd.DataFrame({"y1": y1, "y2": y2, "gamma": gamma, "sig": signal}).dropna()
    if len(df) < 30:
        return None

    g = df["gamma"].abs().clip(lower=1e-6)
    denom = df["y1"] + g * df["y2"]

    # Dollar weights of the (un-signed) spread legs, gross-normalised to 1.
    w1 = df["y1"] / denom
    w2 = -df["gamma"] * df["y2"] / denom

    # Apply the (lagged) trading signal -> actual position weights.
    pos = df["sig"].shift(1).fillna(0)
    pw1 = pos * w1
    pw2 = pos * w2

    ret1 = df["y1"].pct_change().fillna(0)
    ret2 = df["y2"].pct_change().fillna(0)

    # Daily P&L per unit capital: weights set yesterday earn today's leg return.
    gross_ret = pw1.shift(1).fillna(0) * ret1 + pw2.shift(1).fillna(0) * ret2

    # Turnover and transaction costs (sum of |Δ dollar weight| over both legs).
    turnover = (pw1.diff().abs().fillna(pw1.abs())
                + pw2.diff().abs().fillna(pw2.abs()))
    cost = turnover * (tc_bps / 1e4)

    net_ret = gross_ret - cost
    equity = (1 + net_ret).cumprod()
    gross_equity = (1 + gross_ret).cumprod()

    stats = _performance(net_ret, equity, pos, turnover)
    stats_gross = _performance(gross_ret, gross_equity, pos, turnover)
    return {
        "dates": df.index,
        "net_ret": net_ret,
        "gross_ret": gross_ret,
        "equity": equity,
        "gross_equity": gross_equity,
        "position": pos,
        "turnover": turnover,
        "stats": stats,
        "stats_gross": stats_gross,
    }


def _performance(ret: pd.Series, equity: pd.Series, pos: pd.Series,
                 turnover: pd.Series) -> dict:
    r = ret.dropna()
    n = len(r)
    if n == 0 or equity.iloc[-1] <= 0:
        return {"sharpe": np.nan, "ann_return": np.nan, "ann_vol": np.nan,
                "total_return": np.nan, "max_drawdown": np.nan, "n_trades": 0,
                "hit_rate": np.nan, "avg_turnover": np.nan, "exposure": np.nan}
    ann_return = equity.iloc[-1] ** (TRADING_DAYS / n) - 1
    ann_vol = r.std() * np.sqrt(TRADING_DAYS)
    sharpe = (r.mean() / r.std() * np.sqrt(TRADING_DAYS)) if r.std() > 0 else np.nan
    roll_max = equity.cummax()
    max_dd = ((equity - roll_max) / roll_max).min()
    # round-trip trades = number of times position transitions from 0 to +/-1
    trades = int(((pos != 0) & (pos.shift(1).fillna(0) == 0)).sum())
    active = r[pos.shift(0).reindex(r.index).fillna(0) != 0]
    hit = (active > 0).mean() if len(active) else np.nan
    exposure = (pos != 0).mean()
    return {
        "sharpe": float(sharpe),
        "ann_return": float(ann_return),
        "ann_vol": float(ann_vol),
        "total_return": float(equity.iloc[-1] - 1),
        "max_drawdown": float(max_dd),
        "n_trades": trades,
        "hit_rate": float(hit) if hit == hit else np.nan,
        "avg_turnover": float(turnover.mean()),
        "exposure": float(exposure),
    }
