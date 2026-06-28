"""Download and cache adjusted close prices."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yfinance as yf

from config import DATA_DIR, END_DATE, START_DATE


def _cache_path(universe: str) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / f"{universe}_adj_close_{START_DATE}.parquet"


def _metadata_path(universe: str) -> Path:
    return DATA_DIR / f"{universe}_metadata_{START_DATE}.json"


def download_prices(
    tickers: list[str],
    universe: str,
    start: str = START_DATE,
    end: str | None = END_DATE,
    force: bool = False,
) -> pd.DataFrame:
    """
    Download daily adjusted close prices.

    Returns a DataFrame indexed by date with one column per ticker.
    """
    cache = _cache_path(universe)
    if cache.exists() and not force:
        return pd.read_parquet(cache)

    print(f"Downloading {len(tickers)} tickers for {universe} ({start} -> latest)...")

    # yfinance handles batches; chunk to avoid URL limits.
    chunk_size = 80
    frames: list[pd.DataFrame] = []
    failed: list[str] = []

    for i in range(0, len(tickers), chunk_size):
        chunk = tickers[i : i + chunk_size]
        raw = yf.download(
            chunk,
            start=start,
            end=end,
            auto_adjust=True,
            progress=False,
            threads=True,
            group_by="ticker",
        )

        if raw.empty:
            failed.extend(chunk)
            continue

        if len(chunk) == 1:
            ticker = chunk[0]
            if "Close" in raw.columns:
                series = raw["Close"].rename(ticker)
                frames.append(series.to_frame())
            else:
                failed.append(ticker)
            continue

        for ticker in chunk:
            try:
                if ticker in raw.columns.get_level_values(0):
                    close = raw[ticker]["Close"]
                    if close.notna().sum() > 0:
                        frames.append(close.rename(ticker).to_frame())
                    else:
                        failed.append(ticker)
                else:
                    failed.append(ticker)
            except (KeyError, TypeError):
                failed.append(ticker)

    if not frames:
        raise RuntimeError(f"No price data downloaded for {universe}")

    prices = pd.concat(frames, axis=1)
    prices = prices.sort_index()
    prices = prices.loc[:, ~prices.columns.duplicated()]

    # Require at least 252 trading days (~1 year) of data in the sample window.
    min_obs = 252
    valid_cols = prices.columns[prices.notna().sum() >= min_obs]
    prices = prices[valid_cols]
    dropped = set(prices.columns) ^ set(valid_cols)
    if dropped:
        print(f"  Dropped {len(dropped)} tickers with < {min_obs} observations")

    prices.to_parquet(cache)

    meta = {
        "universe": universe,
        "start": start,
        "end": str(prices.index.max().date()),
        "requested_tickers": len(tickers),
        "downloaded_tickers": int(prices.shape[1]),
        "failed_tickers": failed,
        "trading_days": int(prices.shape[0]),
    }
    _metadata_path(universe).write_text(json.dumps(meta, indent=2))
    print(
        f"  Saved {prices.shape[1]} tickers x {prices.shape[0]} days -> {cache.name}"
    )
    return prices


def compute_log_returns(
    prices: pd.DataFrame,
    min_coverage: float = 0.99,
) -> pd.DataFrame:
    """
    Daily log returns with missing-data filtering.

    Drops tickers with less than ``min_coverage`` fraction of valid return
    observations, then removes any remaining incomplete rows. This avoids
    a handful of recent IPOs destroying the usable sample length.
    """
    import numpy as np

    returns = np.log(prices / prices.shift(1))
    coverage = returns.notna().mean()
    keep = coverage[coverage >= min_coverage].index
    dropped = len(returns.columns) - len(keep)
    if dropped:
        print(f"  Dropped {dropped} tickers with < {100*min_coverage:.0f}% return coverage")

    returns = returns[keep]
    returns = returns.replace([np.inf, -np.inf], np.nan).dropna(how="any")
    return returns
