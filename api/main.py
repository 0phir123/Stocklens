# File: api/main.py
from __future__ import annotations
from typing import Any
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from shared.config import settings
from shared.logging import setup_logging
from api.routers.insights import router as insights_router


def create_app() -> FastAPI:
    setup_logging(settings.log_level)
    app = FastAPI(title="StockLens API", version="0.1.0", default_response_class=ORJSONResponse)
    app.include_router(insights_router)
    return app


app = create_app()


async def healthz() -> dict[str, str]:
    return {"status": "ok"}


async def agent_ask(q: str) -> dict[str, Any]:
    return {"answer": f"(stub) you asked: {q}"}


app.add_api_route("/healthz", healthz, methods=["GET"])
app.add_api_route(
    "/v1/agent/ask", agent_ask, methods=["GET"]
)  # keep GET for now; swap to POST later if you prefer
