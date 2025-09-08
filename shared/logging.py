# File: shared/logging.py
from __future__ import annotations
import logging
import sys
from loguru import logger
from types import FrameType
from typing import Optional


class InterceptHandler(logging.Handler):
    """
    Redirect stdlib logging (e.g., uvicorn, fastapi, asyncio) into Loguru.
    This keeps a single logging pipeline.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name  # map stdlib level to Loguru if possible
        except Exception:
            level = "INFO"
        # Find the caller frame to preserve correct file:line in logs
        frame: Optional[FrameType] = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(level: str = "INFO") -> None:
    """
    Configure Loguru:
    - remove default handler
    - add stderr sink
    - intercept stdlib loggers (uvicorn, fastapi)
    """
    logger.remove()
    logger.add(
        sys.stderr,
        level=level.upper(),
        # simple, readable format; we’ll add request_id via middleware context
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "{name}:{function}:{line} - <level>{message}</level>",
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )

    # Intercept common stdlib loggers so everything flows to Loguru
    intercept = InterceptHandler()
    logging.basicConfig(handlers=[intercept], level=logging.getLevelName(level.upper()))
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi", "asyncio"):
        logging.getLogger(name).handlers = [intercept]
        logging.getLogger(name).propagate = False
