# File: shared/di.py
from __future__ import annotations
from typing import Union
from shared.config import settings, load_validation_policy
from services.metrics_service import MetricsService
from services.validation_service import ValidationService

from adapters.metrics.dummy_market_provider import DummyMarketDataAdapter
from adapters.metrics.yahoo_market_provider import YahooMarketDataAdapter
from adapters.metrics.fred_metrics_provider import FREDAsMarketDataAdapter
from adapters.metrics.composite_market_provider import CompositeMarketDataAdapter

validation_service = ValidationService(load_validation_policy())


def _build_market_underlier() -> Union[DummyMarketDataAdapter, YahooMarketDataAdapter]:
    if settings.use_dummy_market:
        return DummyMarketDataAdapter()
    return YahooMarketDataAdapter()


_market_underlier = _build_market_underlier()
_fred_as_market = FREDAsMarketDataAdapter()

_composite = CompositeMarketDataAdapter(
    market_adapter=_market_underlier,
    fred_adapter=_fred_as_market,
)

_metrics_service = MetricsService(market_port=_composite)


def get_metrics_service() -> MetricsService:
    return _metrics_service


def get_validation_service() -> ValidationService:
    return validation_service  # reuse the singleton built above
