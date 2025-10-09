# File: api/main.py
from __future__ import annotations
import time
import uuid
from contextvars import ContextVar
from typing import Callable, Awaitable

from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from shared.config import settings
from shared.logging import setup_logging
from loguru import logger

from api.routers.fetch_data import router as fetch_data_router

# from api.routers.agent import router as agent_router


# Context var to store a per-request id (safe for async)
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


def create_app() -> FastAPI:
    # 1) configure logging early, using your .env-driven level
    setup_logging(settings.log_level)

    # 2) build app
    app = FastAPI(
        title=settings.app_name or "StockLens API",
        version="0.1.0",
        default_response_class=ORJSONResponse,
    )

    # 3) middleware: add request_id, basic access logs with latency and status
    @app.middleware("http")  # type: ignore[misc]
    async def add_request_id_and_log(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # pull X-Request-ID from client or generate
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        token = request_id_ctx.set(rid)  # bind to context for this task
        start = time.perf_counter()

        try:
            logger.bind(request_id=rid).info(
                f"→ {request.method} {request.url.path} qs={request.url.query!s}"
            )
            response: Response = await call_next(request)
        except Exception:
            # log unhandled exceptions with the request id
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.bind(request_id=rid).exception(
                f"✖ {request.method} {request.url.path} failed in {elapsed_ms:.1f} ms"
            )
            raise
        finally:
            request_id_ctx.reset(token)

        # attach the request id to the response
        response.headers["X-Request-ID"] = rid

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.bind(request_id=rid).info(
            f"← {request.method} {request.url.path} {response.status_code} in {elapsed_ms:.1f} ms"
        )
        return response

    @app.get("/healthz")  # type: ignore[misc]
    async def healthz() -> dict[str, str]:
        logger.info("health check")
        return {"status": "ok"}

    # 5) mount your routers
    app.include_router(fetch_data_router)
    # app.include_router(agent_router)
    # agent router later: app.include_router(agent_router)

    logger.info("application startup complete")
    return app


app = create_app()
