# File: adapters/metrics/fred_metrics_provider.py
from __future__ import annotations
from datetime import date
from typing import Optional, List, Literal, Set, Dict
import pandas as pd
from pandas_datareader import data as pdr

from core.metrics.entities import SeriesPoint, Series
from core.metrics.ports import MarketDataPort
from shared.config import settings

Freq = Literal["D", "M", "Q"]


class FREDAsMarketDataAdapter(MarketDataPort):
    """
    Use canonical macro keys and let `freq` control the output:

      macro.gdp   -> FRED: GDPC1 (native Q). If freq=M, derive monthly via linear interpolation.
      macro.cpi   -> FRED: CPIAUCSL (native M).
      macro.baa   -> FRED: BAA (daily -> monthly mean).

    Backward-compatible aliases:
      macro.gdp_q, macro.gdp_m, macro.gdp_real  -> macro.gdp
      macro.baa_yield                            -> macro.baa
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
        df = pdr.DataReader(fred_id, "fred", self._start, self._end, api_key=self._fred_key)
        if isinstance(df, pd.Series):
            return df.to_frame(name="value")
        if df.shape[1] != 1:
            df = df.iloc[:, [0]]
        df.columns = ["value"]
        return df

    @staticmethod
    def _q_to_monthly_linear(df_q: pd.DataFrame) -> pd.DataFrame:
        idx = pd.to_datetime(df_q.index).to_period("Q").to_timestamp("M")
        df = pd.DataFrame(df_q.iloc[:, 0].values, index=idx, columns=["value"])
        return df.resample("M").interpolate(method="linear")

    @staticmethod
    def _daily_to_monthly_mean(df_d: pd.DataFrame) -> pd.DataFrame:
        s = pd.Series(df_d.iloc[:, 0].values, index=pd.to_datetime(df_d.index), name="value")
        return s.resample("M").mean().to_frame()
