"""Cointegration diagnostics used to qualify pairs before trading them."""

from __future__ import annotations

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, coint


def engle_granger(y1: pd.Series, y2: pd.Series) -> dict:
    """Engle-Granger two-step cointegration test (statsmodels coint)."""
    sub = pd.concat([y1, y2], axis=1).dropna()
    score, pvalue, _ = coint(sub.iloc[:, 0], sub.iloc[:, 1])
    return {"eg_stat": float(score), "eg_pvalue": float(pvalue)}


def adf_on_spread(y1: pd.Series, y2: pd.Series) -> dict:
    """Full-sample OLS hedge ratio, then ADF stationarity test on the spread."""
    sub = pd.concat([y1, y2], axis=1).dropna()
    a = sub.iloc[:, 1].values
    b = sub.iloc[:, 0].values
    m2, m1 = a.mean(), b.mean()
    gamma = ((a - m2) * (b - m1)).sum() / ((a - m2) ** 2).sum()
    mu = m1 - gamma * m2
    spread = b - (mu + gamma * a)
    adf_stat, adf_p = adfuller(spread, maxlag=1, regression="c", autolag="AIC")[:2]
    return {
        "ols_gamma": float(gamma),
        "ols_mu": float(mu),
        "adf_stat": float(adf_stat),
        "adf_pvalue": float(adf_p),
        "half_life": half_life(pd.Series(spread)),
    }


def half_life(spread: pd.Series) -> float:
    """Ornstein-Uhlenbeck half-life of mean reversion (in trading days)."""
    s = spread.dropna()
    lag = s.shift(1).dropna()
    delta = (s - s.shift(1)).dropna()
    lag = lag.loc[delta.index]
    x = np.vstack([np.ones(len(lag)), lag.values]).T
    beta = np.linalg.lstsq(x, delta.values, rcond=None)[0][1]
    if beta >= 0:
        return float("inf")
    return float(-np.log(2) / beta)


def summarize_pair(y1: pd.Series, y2: pd.Series) -> dict:
    out = {}
    out.update(engle_granger(y1, y2))
    out.update(adf_on_spread(y1, y2))
    out["correlation"] = float(
        np.corrcoef(y1.pct_change().dropna(), y2.pct_change().dropna())[0, 1]
    )
    return out
