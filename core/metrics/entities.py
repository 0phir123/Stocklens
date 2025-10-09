# File: core/metrics/entities.py
"""
Domain entities for time series.

Defines:
- SeriesPoint: an immutable (date, value) data point.
- Series: a type alias for a list of SeriesPoint items.
"""

from __future__ import annotations

# Standard library
from dataclasses import dataclass
from datetime import date
from typing import List


@dataclass(frozen=True)
class SeriesPoint:
    """
    Atomic time-series data point.

    Attributes
    ----------
    when :
        Calendar date of the observation.
    value :
        Numeric value associated with the date.
    """

    when: date
    value: float


# Type alias: a time series is a list of points.
Series = List[SeriesPoint]
