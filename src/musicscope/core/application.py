"""Application composition root and CLI."""

import argparse
import logging
import time

import glfw

from musicscope.artwork import ArtworkPipeline
from musicscope.audio import AudioAnalyzer, AudioInput, SystemAudioDeviceSelector
from musicscope.config import LOGO_NAMES, AppSettings
from musicscope.config.environment import load_project_environment
from musicscope.core.logo_selector import LogoSelector
from musicscope.core.oscillation_menu import OscillationMenu
from musicscope.graphics import create_context
from musicscope.recognition import RecognitionEngine
from musicscope.recognition.configuration import configured_audd_provider
from musicscope.recognition.service import RecognitionService
from musicscope.recognition.workflow import IdentificationResult, IdentificationWorkflow
from musicscope.renderer import (
    ArtworkRenderer,
    ColorSettings,
    CrtRenderer,
    OscillationSettings,
    OscilloscopeRenderer,
    SettingsMenuRenderer,
    TrackInfoRenderer,
)
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
        recognition_service: RecognitionService | None = None
        try:
            window.open()
            context = create_context()
            oscillation_settings = OscillationSettings()
            color_settings = ColorSettings()
            crt_renderer = CrtRenderer(context, color_settings=color_settings)
            oscilloscope_renderer = OscilloscopeRenderer(
                context, settings=oscillation_settings, color_settings=color_settings
            )
            artwork_renderer = ArtworkRenderer(
                context, logo=self._settings.logo, color_settings=color_settings
            )
            track_info_renderer = TrackInfoRenderer(context, color_settings=color_settings)
            settings_menu_renderer = SettingsMenuRenderer(context, color_settings=color_settings)
            logo_selector = LogoSelector(LOGO_NAMES, self._settings.logo)
            oscillation_menu = OscillationMenu(oscillation_settings, color_settings)
            started_at = time.monotonic()
            provider = configured_audd_provider(self._logger)
            if self._settings.enable_audio:
                device = SystemAudioDeviceSelector().select(self._settings.audio_device)
                if device is None:
                    self._logger.warning(
                        "No system-audio loopback device found; microphone capture is disabled."
                    )
                else:
                    self._logger.info("Capturing system audio from: %s", device.name)
                    if provider is not None:
                        recognition_service = RecognitionService(
                            workflow=IdentificationWorkflow(
                                RecognitionEngine(provider),
                                ArtworkPipeline.default(),
                            ),
                            sample_rate=device.sample_rate,
                            on_identification=self._apply_identification,
                            logger=self._logger,
                        )
                        recognition_service.start()
                    audio_input = AudioInput(
                        analyzer=AudioAnalyzer(sample_rate=device.sample_rate),
                        on_frame=self._scene_manager.update_audio,
                        sample_rate=device.sample_rate,
                        block_size=self._settings.block_size,
                        device=device.name,
                        channels=device.channels,
                        on_samples=(
                            recognition_service.submit_samples
                            if recognition_service is not None
                            else None
                        ),
                        logger=self._logger,
                    )
                    audio_input.start()
            self._logger.info("MusicScope started. Close the window to quit.")
            while not window.should_close:
                window.poll_events()
                keys = window.consume_pressed_keys()
                self._handle_oscillation_menu_shortcuts(keys, oscillation_menu)
                if not oscillation_menu.visible:
                    self._handle_visual_shortcuts(keys, logo_selector, artwork_renderer)
                state = self._scene_manager.state
                width, height = window.framebuffer_size
                context.viewport = (0, 0, width, height)
                elapsed = time.monotonic() - started_at
                crt_renderer.render(state.energy, elapsed)
                oscilloscope_renderer.render(state, elapsed)
                artwork_renderer.render(state, elapsed)
                track_info_renderer.render(state)
                settings_menu_renderer.render(oscillation_menu.visible, oscillation_menu.lines())
                window.present()
        finally:
            if audio_input is not None:
                audio_input.stop()
            if recognition_service is not None:
                recognition_service.stop()
            window.close()

    def _apply_identification(self, result: IdentificationResult) -> None:
        """Publish a recognized track without coupling the renderer to AudD."""
        artwork_path = str(result.artwork.path) if result.artwork is not None else None
        self._scene_manager.set_track(result.track.title, result.track.artist, artwork_path)
        self._logger.info("Recognized: %s — %s", result.track.artist, result.track.title)
        if artwork_path is None:
            self._logger.info("No cover found; keeping the selected centre visual.")

    def _handle_visual_shortcuts(
        self,
        keys: tuple[int, ...],
        logo_selector: LogoSelector,
        artwork_renderer: ArtworkRenderer,
    ) -> None:
        """Apply visual cycling shortcuts received by the window."""
        for key in keys:
            if key in {glfw.KEY_SPACE, glfw.KEY_RIGHT}:
                logo = logo_selector.advance()
            elif key == glfw.KEY_LEFT:
                logo = logo_selector.advance(-1)
            else:
                continue
            artwork_renderer.select_logo(logo)
            self._logger.info("Centre visual selected: %s", logo)

    def _handle_oscillation_menu_shortcuts(
        self,
        keys: tuple[int, ...],
        menu: OscillationMenu,
    ) -> None:
        """Route menu keys without coupling GLFW input to the renderer."""
        for key in keys:
            if key in {glfw.KEY_M, glfw.KEY_SEMICOLON, glfw.KEY_F1}:
                menu.toggle()
                self._logger.info(
                    "Oscillation menu %s.",
                    "opened" if menu.visible else "closed",
                )
            elif menu.visible and key == glfw.KEY_UP:
                menu.move_selection(-1)
            elif menu.visible and key == glfw.KEY_DOWN:
                menu.move_selection(1)
            elif menu.visible and key == glfw.KEY_LEFT:
                menu.adjust_selected(-1)
            elif menu.visible and key == glfw.KEY_RIGHT:
                menu.adjust_selected(1)


def main() -> None:
    """Parse CLI options and run MusicScope."""
    load_project_environment()
    parser = argparse.ArgumentParser(description="Audio-reactive OpenGL visualiser")
    parser.add_argument("--no-audio", action="store_true", help="disable audio capture")
    parser.add_argument("--fullscreen", action="store_true", help="start in fullscreen")
    parser.add_argument("--width", type=int, default=1280, help="window width")
    parser.add_argument("--height", type=int, default=720, help="window height")
    parser.add_argument(
        "--audio-device",
        help="name of the virtual system-audio input device (for example BlackHole)",
    )
    parser.add_argument("--logo", choices=LOGO_NAMES, default="frog")
    args = parser.parse_args()
    settings = AppSettings(
        width=args.width,
        height=args.height,
        fullscreen=args.fullscreen,
        enable_audio=not args.no_audio,
        audio_device=args.audio_device,
        logo=args.logo,
    )
    MusicScopeApp(settings).run()
