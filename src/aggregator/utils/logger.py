from __future__ import annotations

import logging
import os

from rich.logging import RichHandler


def setup_logger(name: str = "researchquantize") -> logging.Logger:
    """Create a shared logger without duplicate handlers."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    handler = RichHandler(rich_tracebacks=True, markup=True)
    handler.setLevel(logger.level)
    handler.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(handler)
    logger.propagate = False
    return logger
