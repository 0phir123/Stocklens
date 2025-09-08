# File: adapters/metrics/composite_market_provider.py'
from __future__ import annotations
from datetime import date
from typing import Optional
from core.metrics.ports import MarketDataPort
from core.metrics.entities import Series


class CompositeMarketDataAdapter(MarketDataPort):
    """
    Delegates:
      - 'macro.*' symbols -> fred_adapter
      - everything else   -> market_adapter (Yahoo or Dummy)
    """

    def __init__(self, market_adapter: MarketDataPort, fred_adapter: MarketDataPort) -> None:
        self._market = market_adapter
        self._fred = fred_adapter

    def get_adjusted_close(
        self,
        symbol: str,
        start: Optional[date] = None,
        end: Optional[date] = None,
        freq: str = "D",
    ) -> Series:
        if symbol.startswith("macro."):
            return self._fred.get_adjusted_close(symbol, start, end, freq)
        return self._market.get_adjusted_close(symbol, start, end, freq)
