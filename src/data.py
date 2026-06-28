"""Data acquisition and caching for the Kalman pairs-trading evaluation.

All prices are daily adjusted close (auto_adjust=True) so that dividends and
splits are already incorporated, which is the right series for a long/short
relative-value strategy.
"""

from __future__ import annotations

import os
import time

import pandas as pd
import yfinance as yf

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data_cache")


def _cache_path(ticker: str) -> str:
    return os.path.join(CACHE_DIR, f"{ticker}.csv")


def get_prices(tickers, start="2010-01-01", end="2025-06-01", force=False) -> pd.DataFrame:
    """Return a DataFrame of adjusted close prices indexed by date.

    Each ticker is cached individually so re-runs do not hit the network.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    if isinstance(tickers, str):
        tickers = [tickers]

    frames = {}
    for t in tickers:
        path = _cache_path(t)
        if os.path.exists(path) and not force:
            s = pd.read_csv(path, index_col=0, parse_dates=True)["close"]
            frames[t] = s
            continue
        # retry with simple backoff
        last_err = None
        for attempt in range(4):
            try:
                raw = yf.download(
                    t, start=start, end=end, progress=False, auto_adjust=True
                )
                if raw is None or raw.empty:
                    raise RuntimeError(f"no data for {t}")
                close = raw["Close"]
                if isinstance(close, pd.DataFrame):
                    close = close.iloc[:, 0]
                close.name = "close"
                close.to_csv(path)
                frames[t] = close
                break
            except Exception as e:  # noqa: BLE001
                last_err = e
                time.sleep(2 * (attempt + 1))
        else:
            raise RuntimeError(f"failed to download {t}: {last_err}")

    df = pd.DataFrame(frames).sort_index()
    df = df.loc[(df.index >= pd.Timestamp(start)) & (df.index <= pd.Timestamp(end))]
    df = df.dropna(how="all")
    return df


def aligned_pair(prices: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    """Return a 2-column frame for a pair with common non-null dates."""
    sub = prices[[a, b]].dropna()
    return sub
