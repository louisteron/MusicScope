"""Logging configuration kept separate from runtime orchestration."""

import logging


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """Return the package logger configured once with a concise formatter."""
    logger = logging.getLogger("musicscope")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(level)
    return logger
