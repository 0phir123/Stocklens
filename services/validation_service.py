# File: services/validation_service.py
from __future__ import annotations

from typing import List, Tuple, cast

from core.metrics.validation import (
    SeriesPoint,
    DataQualityReport,
    ValidationPolicy,
    validate_series,
    Freq,  # <-- import the Literal type
)
from shared.config import load_validation_policy


class ValidationService:
    """Thin wrapper so other services/routers can depend on an object."""

    def __init__(self, policy: ValidationPolicy | None = None) -> None:
        self.policy = policy or load_validation_policy()

    def run(
        self, points: List[SeriesPoint], freq: str, symbol_key: str
    ) -> Tuple[List[SeriesPoint], DataQualityReport]:
        # Normalize to {"D","M","Q"} and cast to the Freq Literal for mypy
        normalized: str = (
            "D" if freq.upper().startswith("D") else ("Q" if freq.upper().startswith("Q") else "M")
        )
        f: Freq = cast(Freq, normalized)
        return validate_series(points, f, symbol_key, self.policy)
