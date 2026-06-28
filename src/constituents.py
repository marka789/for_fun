"""Fetch S&P 500 and Nasdaq-100 constituent tickers."""

from __future__ import annotations

import io
import re

import pandas as pd
import requests

WIKI_SP500 = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
WIKI_NASDAQ100 = "https://en.wikipedia.org/wiki/Nasdaq-100"


def _normalize_ticker(symbol: str) -> str:
    """Convert symbols for yfinance (e.g. BRK.B -> BRK-B)."""
    return symbol.strip().replace(".", "-")


def _read_wiki_table(url: str, table_index: int = 0) -> pd.DataFrame:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; covariance-pca-rmt/1.0; +https://github.com)"
        )
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    tables = pd.read_html(io.StringIO(response.text))
    return tables[table_index]


def get_sp500_tickers() -> list[str]:
    """Return current S&P 500 symbols."""
    df = _read_wiki_table(WIKI_SP500, table_index=0)
    symbol_col = "Symbol" if "Symbol" in df.columns else df.columns[0]
    tickers = [_normalize_ticker(s) for s in df[symbol_col].astype(str)]
    return sorted(set(tickers))


def get_nasdaq100_tickers() -> list[str]:
    """Return current Nasdaq-100 symbols."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; covariance-pca-rmt/1.0; +https://github.com)"
        )
    }
    response = requests.get(WIKI_NASDAQ100, headers=headers, timeout=30)
    response.raise_for_status()
    tables = pd.read_html(io.StringIO(response.text))

    constituents = None
    for table in tables:
        cols = [str(c) for c in table.columns]
        if "Ticker" in cols and "Company" in cols:
            constituents = table
            break

    if constituents is None:
        raise ValueError("Could not locate Nasdaq-100 constituents table on Wikipedia")

    tickers = [_normalize_ticker(s) for s in constituents["Ticker"].astype(str)]
    tickers = [t for t in tickers if re.fullmatch(r"[A-Z0-9\-]+", t)]
    return sorted(set(tickers))
