"""Application composition root and CLI."""

import argparse
import logging

from musicscope.audio import AudioAnalyzer, AudioInput
from musicscope.config import AppSettings
from musicscope.graphics import create_context
from musicscope.renderer import BackgroundRenderer, SpectrumRenderer
from musicscope.scene import SceneManager
from musicscope.utils.logging import configure_logging
from musicscope.window import GlfwWindow


class MusicScopeApp:
    """Compose services and own the application's startup and shutdown."""

    def __init__(self, settings: AppSettings, logger: logging.Logger | None = None) -> None:
        self._settings = settings
        self._logger = logger or configure_logging()
        self._scene_manager = SceneManager()

    def run(self) -> None:
        """Open the window and run until the user closes it."""
        window = GlfwWindow(
            self._settings.title,
            self._settings.width,
            self._settings.height,
            self._settings.fullscreen,
        )
        audio_input: AudioInput | None = None
        try:
            window.open()
            context = create_context()
            background_renderer = BackgroundRenderer(context)
            spectrum_renderer = SpectrumRenderer(context)
            if self._settings.enable_audio:
                audio_input = AudioInput(
                    analyzer=AudioAnalyzer(),
                    on_frame=self._scene_manager.update_audio,
                    sample_rate=self._settings.sample_rate,
                    block_size=self._settings.block_size,
                    logger=self._logger,
                )
                audio_input.start()
            self._logger.info("MusicScope started. Close the window to quit.")
            while not window.should_close:
                state = self._scene_manager.state
                background_renderer.render(state, window.framebuffer_size)
                spectrum_renderer.render(state)
                window.present()
                window.poll_events()
        finally:
            if audio_input is not None:
                audio_input.stop()
            window.close()


def main() -> None:
    """Parse CLI options and run MusicScope."""
    parser = argparse.ArgumentParser(description="Audio-reactive OpenGL visualiser")
    parser.add_argument("--no-audio", action="store_true", help="disable audio capture")
    parser.add_argument("--fullscreen", action="store_true", help="start in fullscreen")
    parser.add_argument("--width", type=int, default=1280, help="window width")
    parser.add_argument("--height", type=int, default=720, help="window height")
    args = parser.parse_args()
    settings = AppSettings(
        width=args.width,
        height=args.height,
        fullscreen=args.fullscreen,
        enable_audio=not args.no_audio,
    )
    MusicScopeApp(settings).run()
