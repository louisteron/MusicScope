"""Native optical-disc ejection behind a small platform adapter."""

import logging
import subprocess
import sys
from collections.abc import Callable

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


class CdEjector:
    """Eject the optical disc using the host operating system's native utility."""

    def __init__(
        self,
        device: str | None = None,
        platform: str = sys.platform,
        run: CommandRunner = subprocess.run,
        logger: logging.Logger | None = None,
    ) -> None:
        self._device = device
        self._platform = platform
        self._run = run
        self._logger = logger or logging.getLogger("musicscope")

    def eject(self) -> bool:
        """Request an ejection and return whether the system accepted it."""
        try:
            self._run(
                self._command(),
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            self._logger.warning("CD ejection is unavailable on this system.")
            return False
        except subprocess.CalledProcessError as error:
            detail = error.stderr.strip() if error.stderr else "native eject command failed"
            self._logger.warning("CD ejection failed: %s", detail)
            return False
        self._logger.info("CD ejected.")
        return True

    def _command(self) -> list[str]:
        """Build the native command without relying on a shell."""
        if self._platform == "darwin":
            return ["drutil", "tray", "eject"]
        if self._platform.startswith("win"):
            return [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                "(New-Object -ComObject WMPlayer.OCX).cdromCollection.Item(0).Eject()",
            ]
        return ["eject", *([self._device] if self._device is not None else [])]
