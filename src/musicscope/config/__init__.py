"""Application configuration."""

from musicscope.config.environment import load_project_environment
from musicscope.config.settings import LOGO_NAMES, AppSettings, RecognitionMode

__all__ = ["LOGO_NAMES", "AppSettings", "RecognitionMode", "load_project_environment"]
