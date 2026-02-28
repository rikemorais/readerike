"""Logging configuration for readerike."""

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger with a structured format.

    Args:
        level: Log level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )

    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Avoid adding duplicate handlers on re-import (e.g. in tests)
    if not root.handlers:
        root.addHandler(handler)
