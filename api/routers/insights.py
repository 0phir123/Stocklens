from __future__ import annotations  # lazy annotations

from datetime import date  # used in DTO typing
from typing import Optional, List  # Optional[T], List[T] for DTO fields

from fastapi import APIRouter, HTTPException, Query  # FastAPI routing & validation primitives

# APIRouter: define a namespaced group of endpoints
# HTTPException: raise proper HTTP errors (status code + detail)
# Query: declare/validate query-string params

from pydantic import BaseModel, Field  # DTOs (data transfer objects) for request/response

# BaseModel: schema + validation + serialization
# Field: add descriptions/defaults/constraints to model fields

from shared.di import get_metrics_service  # import service getter from our DI module

router = APIRouter(
    prefix="/v1/insights", tags=["insights"]
)  # group endpoints under path prefix + docs tag


class PricePointDTO(BaseModel):  # RESPONSE DTO for a single point (wire format)
    when: date = Field(
        ..., description="Calendar date"
    )  # '...' means required; description shows in OpenAPI docs
    value: float = Field(..., description="Adjusted close")  # required float


class PricesResponseDTO(BaseModel):  # top-level response DTO
    symbol: str  # the requested symbol
    points: List[PricePointDTO]  # list of point DTOs


def get_prices(
    symbol: str = Query(..., min_length=1),  # required query param 'symbol'; min length 1
    start: Optional[date] = Query(None),  # optional date param; FastAPI parses ISO date strings
    end: Optional[date] = Query(None),  # optional date param
    freq: str = Query(
        "D", pattern="^[DMQdmq]$"
    ),  # default "D"; regex restricts to D/M/Q (case-insensitive)
) -> PricesResponseDTO:
    svc = get_metrics_service()  # acquire the service via DI (could also use Depends)
    try:
        series = svc.get_prices(  # call our use-case with validated inputs
            symbol=symbol,
            start=start,
            end=end,
            freq=freq.upper(),  # normalize to uppercase for adapter logic
        )
    except ValueError as e:  # map domain/input errors to HTTP 400 Bad Request
        raise HTTPException(status_code=400, detail=str(e))

    return PricesResponseDTO(  # map domain objects → DTOs for the wire
        symbol=symbol,
        points=[PricePointDTO(when=p.when, value=p.value) for p in series],
    )


router.add_api_route(
    "/prices",
    get_prices,
    methods=["GET"],
    response_model=PricesResponseDTO,
)
