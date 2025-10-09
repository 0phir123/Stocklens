# File: core/metrics/ports.py
"""
Ports (interfaces) for metrics domain.

Exposes:
- MarketDataPort: structural interface for adapters that provide adjusted-close
  time series for a given symbol and optional date range/frequency.
"""

from __future__ import annotations

# Standard library
from datetime import date
from typing import Optional
from typing import Protocol
from typing import runtime_checkable

# Local application
from .entities import Series


@runtime_checkable
class MarketDataPort(Protocol):
    """
    Interface for market data providers that can return adjusted-close series.

    Implementations should fetch a price-like series for the given `symbol`,
    optionally constrained by `start`/`end` dates and resampled to the desired
    `freq` ("D" daily, "M" monthly, "Q" quarterly).
    """

    def get_adjusted_close(
        self,
        symbol: str,
        start: Optional[date] = None,
        end: Optional[date] = None,
        freq: str = "D",
    ) -> Series:
        """
        Retrieve an adjusted close-like time series.

        Parameters
        ----------
        symbol:
            Ticker or key recognized by the implementation.
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
        """
        ...
