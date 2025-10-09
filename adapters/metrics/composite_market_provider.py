# File: adapters/metrics/composite_market_provider.py
"""
Composite market data adapter.

This module defines a thin router that delegates price/series requests
to the appropriate market data adapter based on the symbol prefix.

Current routing rule:
  - Symbols starting with 'macro.' are handled by the FRED adapter.
  - All other symbols are handled by the default market adapter (e.g., Yahoo/Dummy).

The simplicity is intentional while there are only two backends. If/when
more backends are added, this class is the single place to evolve the
routing logic (e.g., a prefix map or predicate-based rules).
"""

from __future__ import annotations

# Standard library
from datetime import date
from typing import Optional

# Local application imports
from core.metrics.entities import Series
from core.metrics.ports import MarketDataPort


class CompositeMarketDataAdapter(MarketDataPort):
    """
    Delegate market data queries to one of two adapters.

    Routing policy:
        - 'macro.*'  -> `fred_adapter`
        - otherwise  -> `market_adapter`

    This class implements the `MarketDataPort` so it can be used anywhere a
    concrete adapter is expected, while hiding the routing decision.
    """

    _MACRO_PREFIX = "macro."

    def __init__(self, market_adapter: MarketDataPort, fred_adapter: MarketDataPort) -> None:
        """
        Initialize the composite adapter.

        Parameters
        ----------
        market_adapter:
            Adapter used for non-`macro.*` symbols (e.g., Yahoo/Dummy).
        fred_adapter:
            Adapter used for `macro.*` symbols.
        """
        self._market = market_adapter
        self._fred = fred_adapter

    def _pick_adapter(self, symbol: str) -> MarketDataPort:
        """Choose the underlying adapter for a given symbol."""
        return self._fred if symbol.startswith(self._MACRO_PREFIX) else self._market

    def get_adjusted_close(
        self,
        symbol: str,
        start: Optional[date] = None,
        end: Optional[date] = None,
        freq: str = "D",
    ) -> Series:
        """
        Return an adjusted close time series for the given symbol.

        Parameters
        ----------
        symbol:
            Instrument identifier. Symbols beginning with 'macro.' are routed to FRED.
        start:
            Optional start date filter.
        end:
            Optional end date filter.
        freq:
            Aggregation frequency (e.g., 'D', 'W', 'M').

        Returns
        -------
        Series
            The time series returned by the selected underlying adapter.
        """
        adapter = self._pick_adapter(symbol)
        return adapter.get_adjusted_close(symbol, start, end, freq)
