# File: core/metrics/ports.py
from __future__ import annotations  # lazy type hints (see above)

from typing import Protocol, Optional, runtime_checkable  # import typing helpers

# Protocol: define structural interfaces (duck-typed)
# Optional[T]: T or None
# runtime_checkable: allows isinstance(x, ThisProtocol) at runtime


from datetime import date  # date type for parameters
from .entities import Series  # import domain type alias for return type

# ^ Relative import: '.' means current package (core/metrics)


@runtime_checkable  # enable runtime isinstance checks on this Protocol
class MarketDataPort(Protocol):  # define a Protocol (interface) named MarketDataPort
    def get_adjusted_close(  # method signature the port guarantees exists
        self,  # instance method ('self' is required by Python)
        symbol: str,  # ticker symbol (required string)
        start: Optional[date] = None,  # optional start date; default None = no lower bound
        end: Optional[date] = None,  # optional end date; default None = no upper bound
        freq: str = "D",  # frequency hint: "D" daily, "M" monthly, "Q" quarterly
    ) -> Series: ...  # returns a Series (our domain list of points); '...' = stub body
