# File: api/routers/fetch_data.py
from __future__ import annotations

# ---- stdlib
from datetime import date, datetime, time
from typing import Optional, List, Dict, Any

# ---- third-party
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

# ---- local
from shared.di import get_metrics_service, get_validation_service
from services.validation_service import ValidationService
from core.metrics.validation import SeriesPoint

router = APIRouter(prefix="/v1/fetch_data", tags=["fetch_data"])


class PricePointDTO(BaseModel):
    """RESPONSE DTO for a single point (wire format)."""

    when: date = Field(..., description="Calendar date (period end for M/Q)")
    value: float = Field(..., description="Series value (price or macro)")


class PricesResponseDTO(BaseModel):
    """Top-level response DTO for /prices."""

    symbol: str
    points: List[PricePointDTO]


class PricesWithValidationResponseDTO(PricesResponseDTO):
    """Response DTO for /prices_with_validation (adds report)."""

    report: Dict[str, Any]


def get_prices(
    symbol: str = Query(..., min_length=1),
    start: Optional[date] = Query(None),
    end: Optional[date] = Query(None),
    freq: str = Query("D", pattern="^[DMQdmq]$"),
) -> PricesResponseDTO:
    svc = get_metrics_service()
    try:
        series = svc.get_prices(symbol=symbol, start=start, end=end, freq=freq.upper())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return PricesResponseDTO(
        symbol=symbol,
        points=[PricePointDTO(when=p.when, value=p.value) for p in series],
    )


def _normalize_ts(d: date | datetime) -> datetime:
    """Normalize date/datetime to a naive datetime at midnight (00:00)."""
    return d if isinstance(d, datetime) else datetime.combine(d, time.min)


def get_prices_with_validation(
    symbol: str = Query(..., min_length=1),
    start: Optional[date] = Query(None),
    end: Optional[date] = Query(None),
    freq: str = Query("D", pattern="^[DMQdmq]$"),
    val_svc: ValidationService = Depends(get_validation_service),
) -> PricesWithValidationResponseDTO:
    # 1) Fetch raw prices
    svc = get_metrics_service()
    try:
        series = svc.get_prices(symbol=symbol, start=start, end=end, freq=freq.upper())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2) Convert to SeriesPoint (date -> datetime 00:00)
    points = [SeriesPoint(ts=_normalize_ts(p.when), value=p.value) for p in series]

    # 3) Run validation
    clean, report = val_svc.run(points, freq.upper(), symbol)

    # 4) Map back to DTOs
    return PricesWithValidationResponseDTO(
        symbol=symbol,
        points=[PricePointDTO(when=p.ts.date(), value=p.value) for p in clean],
        report=report.__dict__,
    )


router.add_api_route("/prices", get_prices, methods=["GET"], response_model=PricesResponseDTO)
router.add_api_route(
    "/prices_with_validation",
    get_prices_with_validation,
    methods=["GET"],
    response_model=PricesWithValidationResponseDTO,
)
