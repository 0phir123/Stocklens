# File: shared/logging.py
from loguru import logger
import sys

def setup_logging(level: str = "INFO") -> None:
    logger.remove()  # Remove the default logger
    logger.add(sys.stderr, level=level, 
               enqueue=True, backtrace=False, diagnose=False)
