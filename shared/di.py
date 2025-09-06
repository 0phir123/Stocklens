from __future__ import annotations  # lazy annotations

from adapters.metrics.dummy_market_provider import DummyMarketDataAdapter

# ^ import the concrete adapter *we choose to use now*

from services.metrics_service import MetricsService  # import the service type

_market_adapter = DummyMarketDataAdapter()  # build a singleton adapter instance
# ^ global module-level variables act as simple singletons in this minimal setup

_metrics_service = MetricsService(
    market_port=_market_adapter
)  # inject adapter into service (constructor injection)


def get_metrics_service() -> MetricsService:  # expose a getter for routes (or FastAPI Depends)
    return _metrics_service


# ^ if you want to swap providers globally later, change the instantiation above (1 place only)
