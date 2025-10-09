# File: adapters/metrics/yahoo_market_provider.py
"""
Yahoo Finance–backed market data adapter.

This module implements `MarketDataPort` using `yfinance`. It downloads daily,
auto-adjusted prices and resamples to the requested frequency (D/M/Q), returning
domain `SeriesPoint` items sorted by date and deduplicated.

Notes
-----
- Uses `settings.data_start` / `settings.data_end` as defaults when start/end
  are not provided.
- For symbols with multi-indexed columns, prefers 'Adj Close' then 'Close'.
"""

from __future__ import annotations

# Standard library
from datetime import date
from typing import List
from typing import Optional

# Third-party
import pandas as pd
import yfinance as yf

# Local application
from core.metrics.entities import Series
from core.metrics.entities import SeriesPoint
from core.metrics.ports import MarketDataPort
from shared.config import settings


class YahooMarketDataAdapter(MarketDataPort):
    """
    Market data adapter that retrieves price series via Yahoo Finance.

    Workflow:
      1. Download daily auto-adjusted prices.
      2. Normalize to a single 'value' column (Adj Close preferred).
      3. Resample to D/M/Q.
      4. Slice by start/end if provided.
      5. Return as a list of `SeriesPoint` (sorted, deduplicated).
    """

    def get_adjusted_close(
        self,
        symbol: str,
        start: Optional[date] = None,
        end: Optional[date] = None,
        freq: str = "D",
    ) -> Series:
        """
        Retrieve an adjusted close-like series for a Yahoo symbol.

        Parameters
        ----------
        symbol:
            Ticker symbol understood by Yahoo Finance.
        start:
            Optional start date (inclusive).
        end:
            Optional end date (inclusive).
        freq:
            Output frequency: "D", "M", or "Q".

        Returns
        -------
        Series
            A list of `SeriesPoint` entries sorted by date.

        Raises
        ------
        ValueError
            If symbol is empty, date range is invalid, or `freq` is not D/M/Q.
        """
        # ---- guardrails ----
        if not symbol:
            raise ValueError("symbol is required")
        if start and end and start > end:
            raise ValueError("start must be <= end")
        f = freq.upper()
        if f not in ("D", "M", "Q"):
            raise ValueError("freq must be one of D/M/Q")

        # ---- defaults from config ----
        start_dt = pd.to_datetime(start or settings.data_start)
        end_dt = pd.to_datetime(end or settings.data_end)

        # ---- fetch daily auto-adjusted prices ----
        df = yf.download(
            symbol,
            start=start_dt,
            end=end_dt,
            interval="1d",
            auto_adjust=True,
            progress=False,
        )

        if df is None or len(df) == 0:
            return []

        # ---- normalize to one column 'value' (Adj Close if present) ----
        if isinstance(df.columns, pd.MultiIndex):
            if ("Adj Close", symbol) in df.columns:
                s = df[("Adj Close", symbol)]
            elif ("Close", symbol) in df.columns:
                s = df[("Close", symbol)]
            else:
                s = df.iloc[:, 0]
        else:
            if "Adj Close" in df.columns:
                s = df["Adj Close"]
            elif "Close" in df.columns:
                s = df["Close"]
            else:
                s = df.iloc[:, 0]

        s = pd.Series(s, name="value")
        s.index = pd.to_datetime(s.index)
        # ---- resample to target D/M/Q ----
        if f == "D":
            rs = s.asfreq("D", method="pad")  # pad gaps to calendar days
        elif f == "M":
            rs = s.resample("M").last()  # month-end close
        else:  # "Q"
            rs = s.resample("Q").last()
            rs.index = rs.index.to_period("Q").to_timestamp("M")  # align to month-end

        # ---- slice inclusive by date if explicit start/end passed ----
        if start:
            rs = rs[rs.index.date >= start]
        if end:
            rs = rs[rs.index.date <= end]

        # ---- map to domain objects (sorted, dedup) ----
        points: List[SeriesPoint] = []
        seen: set[date] = set()
        for ts, val in rs.sort_index().items():
            d = ts.date()
            if d in seen or pd.isna(val):
                continue
            seen.add(d)
            points.append(SeriesPoint(when=d, value=float(val)))

        return points
