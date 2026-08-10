"""Structured run progress logging."""
import logging 
import os 
import sys

_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(
    stream=sys.stdout,
    level=getattr(logging, _LOG_LEVEL, logging.INFO),
    format="[%(levelname)s] %(message)s",
)

_logger = logging.getLogger("update_tf_modules")

def info(message: str) -> None:
    _logger.info(message)


def warn(message: str) -> None:
    _logger.warning(message)


def skip(message: str) -> None:
    _logger.info("[SKIP] %s", message)


def error(message: str) -> None:
    _logger.error(message)
