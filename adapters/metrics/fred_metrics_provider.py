# File: adapters/metrics/fred_metrics_provider.py
"""
FRED-backed market data adapter.

This module provides a concrete implementation of `MarketDataPort` that serves
macro-economic time series from the Federal Reserve Economic Data (FRED)
service using canonical `macro.*` symbols.

Supported canonical symbols:
  - macro.gdp  -> FRED: GDPC1 (native quarterly). Can be derived monthly by linear interpolation.
  - macro.cpi  -> FRED: CPIAUCSL (native monthly).
  - macro.baa  -> FRED: BAA (native daily; aggregated to monthly mean).

Aliases (backward compatibility) map to the canonical keys, e.g.:
  - macro.gdp_q, macro.gdp_m, macro.gdp_real  -> macro.gdp
  - macro.baa_yield                            -> macro.baa

Frequency handling:
  - The `freq` parameter controls resampling to "D" (daily), "M" (monthly), or "Q" (quarterly).
  - Native series are aligned to period-end for monthly/quarterly before resampling.
"""

from __future__ import annotations

# Standard library
from datetime import date
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Set

# Third-party
import pandas as pd
from pandas_datareader import data as pdr

# Local application
from core.metrics.entities import Series
from core.metrics.entities import SeriesPoint
from core.metrics.ports import MarketDataPort
from shared.config import settings

Freq = Literal["D", "M", "Q"]


class FREDAsMarketDataAdapter(MarketDataPort):
    """
    Market data adapter that retrieves macro series from FRED.

    The adapter accepts `macro.*` symbols and routes them to the appropriate
    FRED series IDs, handling interpolation/aggregation when needed and
    resampling to the requested output frequency.

    Notes
    -----
    - Only `macro.*` symbols are supported; other symbols raise `ValueError`.
    - The API key is taken from `settings.fred_api_key` unless provided directly.
    - Date bounds default to `settings.data_start` / `settings.data_end` if not passed.
    """

    _CANONICAL: Set[str] = {"macro.gdp", "macro.cpi", "macro.baa"}
    _ALIASES: Dict[str, str] = {
        "macro.gdp_q": "macro.gdp",
        "macro.gdp_m": "macro.gdp",
        "macro.gdp_real": "macro.gdp",
        "macro.baa_yield": "macro.baa",
    }

    def __init__(
        self,
        fred_api_key: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> None:
        """
        Initialize the FRED adapter.

        Parameters
        ----------
        fred_api_key:
            Optional FRED API key. Falls back to `settings.fred_api_key` if not provided.
        start:
            Optional ISO date string for the lower bound (inclusive). Defaults to settings or 1990-01-01.
        end:
            Optional ISO date string for the upper bound (inclusive). Defaults to settings or 2025-12-31.
        """
        self._fred_key = fred_api_key or getattr(settings, "fred_api_key", "") or None
        self._start = pd.to_datetime(start or getattr(settings, "data_start", "1990-01-01"))
        self._end = pd.to_datetime(end or getattr(settings, "data_end", "2025-12-31"))

    # ---- MarketDataPort ----
    def get_adjusted_close(
        self,
        symbol: str,
        start: Optional[date] = None,
        end: Optional[date] = None,
        freq: str = "D",
    ) -> Series:
        """
        Retrieve an adjusted close-like series for a macro symbol.

        Parameters
        ----------
        symbol:
            Macro symbol starting with `macro.` (e.g., `macro.gdp`, `macro.cpi`, `macro.baa`).
            Aliases are supported and normalized to canonical keys.
        start:
            Optional start date (inclusive) to filter the result.
        end:
            Optional end date (inclusive) to filter the result.
        freq:
            Output frequency: one of "D", "M", or "Q".

        Returns
        -------
        Series
            A list of `SeriesPoint` values sorted by date.

        Raises
        ------
        ValueError
            If `symbol` is empty, not a `macro.*` key, not supported, if `freq` is invalid,
            or if the date range is inconsistent.
        """
        if not symbol:
            raise ValueError("symbol is required")
        if not symbol.startswith("macro."):
            raise ValueError("FREDAsMarketDataAdapter only supports symbols starting with 'macro.'")

        # Normalize to canonical
        canonical = self._ALIASES.get(symbol, symbol)
        if canonical not in self._CANONICAL:
            supported = sorted(list(self._CANONICAL | set(self._ALIASES.keys())))
            raise ValueError(f"Unsupported macro symbol '{symbol}'. Try one of: {supported}")

        f = freq.upper()
        if f not in ("D", "M", "Q"):
            raise ValueError("freq must be one of D/M/Q")
        if start and end and start > end:
            raise ValueError("start must be <= end")

        # 1) fetch native
        if canonical == "macro.cpi":
            df = self._fetch_one_col("CPIAUCSL")  # native M
            native: Freq = "M"

        elif canonical == "macro.gdp":
            df_q = self._fetch_one_col("GDPC1")  # native Q
            native = "Q"
            # if monthly requested OR alias macro.gdp_m used, derive monthly
            if f == "M" or symbol == "macro.gdp_m":
                df = self._q_to_monthly_linear(df_q)
                native = "M"
            else:
                df = df_q

        elif canonical == "macro.baa":
            df_d = self._fetch_one_col("BAA")  # daily -> monthly mean
            df = self._daily_to_monthly_mean(df_d)
            native = "M"

        else:
            # Defensive; should not be reachable due to earlier checks.
            raise ValueError(f"unsupported macro symbol: {symbol}")

        # 2) align native to period end for M/Q
        if native == "M":
            df.index = pd.to_datetime(df.index).to_period("M").to_timestamp("M")
        elif native == "Q":
            df.index = pd.to_datetime(df.index).to_period("Q").to_timestamp("M")
        else:
            df.index = pd.to_datetime(df.index)

        # 3) resample to requested freq
        if f != native:
            if f == "D":
                df = df.resample("D").ffill()
            elif f == "M":
                df = df.resample("M").ffill()
            elif f == "Q":
                df = df.resample("Q").last()
                df.index = df.index.to_period("Q").to_timestamp("M")

        # 4) inclusive slice
        if start:
            df = df[df.index.date >= start]
        if end:
            df = df[df.index.date <= end]

        # 5) map to SeriesPoint[]
        out: List[SeriesPoint] = []
        seen: set[date] = set()
        for ts, val in df.sort_index()["value"].items():
            d = ts.date()
            if d in seen or pd.isna(val):
                continue
            seen.add(d)
            out.append(SeriesPoint(when=d, value=float(val)))
        return out

    # ---- helpers ----
    def _fetch_one_col(self, fred_id: str) -> pd.DataFrame:
        """
        Fetch a single-column FRED series as a DataFrame named 'value'.

        Parameters
        ----------
        fred_id:
            The FRED series identifier (e.g., 'GDPC1', 'CPIAUCSL', 'BAA').

        Returns
        -------
        pandas.DataFrame
            A dataframe with a DateTimeIndex and one column named 'value'.
        """
        df = pdr.DataReader(fred_id, "fred", self._start, self._end, api_key=self._fred_key)
        if isinstance(df, pd.Series):
            return df.to_frame(name="value")
        if df.shape[1] != 1:
            df = df.iloc[:, [0]]
        df.columns = ["value"]
        return df

    @staticmethod
    def _q_to_monthly_linear(df_q: pd.DataFrame) -> pd.DataFrame:
        """
        Derive a monthly series from a quarterly series by linear interpolation.

        Parameters
        ----------
        df_q:
            Quarterly dataframe with a single value column.

        Returns
        -------
        pandas.DataFrame
            Monthly dataframe, linearly interpolated between quarter endpoints.
        """
        idx = pd.to_datetime(df_q.index).to_period("Q").to_timestamp("M")
        df = pd.DataFrame(df_q.iloc[:, 0].values, index=idx, columns=["value"])
        return df.resample("M").interpolate(method="linear")

    @staticmethod
    def _daily_to_monthly_mean(df_d: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate a daily series to monthly mean.

        Parameters
        ----------
        df_d:
            Daily dataframe with a single value column.

        Returns
        -------
        pandas.DataFrame
            Monthly dataframe with mean aggregation.
        """
        s = pd.Series(df_d.iloc[:, 0].values, index=pd.to_datetime(df_d.index), name="value")
        return s.resample("M").mean().to_frame()
