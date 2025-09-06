from __future__ import annotations  # lazy annotations

from datetime import date  # type for parameters
from typing import Optional  # Optional[T] for nullable args

from core.metrics.entities import Series  # domain return type
from core.metrics.ports import MarketDataPort  # depend on Port (interface), not on concrete adapter


class MetricsService:  # define the service (single responsibility: orchestrate this use-case)
    def __init__(self, market_port: MarketDataPort):
        self._market = market_port  # constructor injection of the Port (DI-friendly, testable)

    def get_prices(  # public use-case method the API calls
        self,
        symbol: str,
        start: Optional[date] = None,
        end: Optional[date] = None,
        freq: str = "D",
    ) -> Series:  # returns domain Series
        if (
            not symbol or not symbol.strip()
        ):  # business validation: symbol cannot be empty/whitespace
            raise ValueError("symbol is required")

        # Here is where you'd add caching, rate limits, retries, policy strategies, etc.
        return (
            self._market.get_adjusted_close(  # delegate to the Port; service stays vendor-agnostic
                symbol=symbol,
                start=start,
                end=end,
                freq=freq,
            )
        )
