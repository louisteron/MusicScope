"""Application configuration."""

from musicscope.config.environment import load_project_environment
from musicscope.config.settings import LOGO_NAMES, AppSettings

__all__ = ["LOGO_NAMES", "AppSettings", "load_project_environment"]
