"""Runtime configuration for recognition providers."""

import logging

from musicscope.recognition.audd import AudDCredentials, AudDProvider


def configured_audd_provider(logger: logging.Logger) -> AudDProvider | None:
    """Create AudD when configured, otherwise leave recognition disabled."""
    try:
        credentials = AudDCredentials.from_environment()
    except RuntimeError:
        logger.warning("⚠ AudD disabled (missing API token)")
        return None
    logger.info("✓ AudD provider loaded")
    return AudDProvider(credentials, logger=logger)
