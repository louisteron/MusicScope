"""Application composition root and CLI."""

import argparse
import logging
import time

import glfw
import numpy as np

from musicscope.artwork import ArtworkPipeline
from musicscope.audio import (
    AudioAnalyzer,
    AudioInput,
    AudioOutput,
    AudioOutputDevice,
    AudioOutputDeviceSelector,
    AudioOutputSettings,
    SystemAudioDeviceSelector,
)
from musicscope.config import LOGO_NAMES, AppSettings, RecognitionMode
from musicscope.config.environment import load_project_environment
from musicscope.core.oscillation_menu import OscillationMenu
from musicscope.core.recognition_settings import RecognitionSettings
from musicscope.graphics import create_context
from musicscope.recognition import RecognitionEngine
from musicscope.recognition.cd import MusicBrainzCdLookup
from musicscope.recognition.cd_service import CdMetadataService
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
        audio_output: AudioOutput | None = None
        recognition_service: RecognitionService | None = None
        cd_metadata_service: CdMetadataService | None = None
        capture_device = None
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
            output_settings = AudioOutputSettings(AudioOutputDeviceSelector().available())
            recognition_settings = RecognitionSettings(self._settings.recognition_mode)

            def select_audio_output(device: AudioOutputDevice | None) -> None:
                if audio_output is None:
                    self._logger.warning("Audio output cannot start without an input source.")
                    return
                audio_output.select(device)

            def select_recognition_mode(mode: RecognitionMode) -> None:
                nonlocal cd_metadata_service, recognition_service
                if recognition_service is not None:
                    recognition_service.stop()
                    recognition_service = None
                if cd_metadata_service is not None:
                    cd_metadata_service.stop()
                    cd_metadata_service = None
                if mode is RecognitionMode.OFF:
                    self._logger.info("Music recognition disabled.")
                    return
                if mode is RecognitionMode.LOCAL_CD:
                    cd_metadata_service = CdMetadataService(
                        lookup=MusicBrainzCdLookup(),
                        artwork_pipeline=ArtworkPipeline.default(),
                        on_identification=self._apply_identification,
                        device=self._settings.cd_device,
                        logger=self._logger,
                    )
                    cd_metadata_service.start()
                    self._logger.info("Local CD metadata recognition enabled (AudD is disabled).")
                    return
                if capture_device is None:
                    self._logger.warning("AudD needs an active audio input source.")
                    return
                provider = configured_audd_provider(self._logger)
                if provider is None:
                    return
                recognition_service = RecognitionService(
                    workflow=IdentificationWorkflow(
                        RecognitionEngine(provider),
                        ArtworkPipeline.default(),
                    ),
                    sample_rate=capture_device.sample_rate,
                    on_identification=self._apply_identification,
                    logger=self._logger,
                )
                recognition_service.start()

            oscillation_menu = OscillationMenu(
                oscillation_settings,
                color_settings,
                output_settings=output_settings,
                on_output_change=select_audio_output,
                recognition_settings=recognition_settings,
                on_recognition_change=select_recognition_mode,
            )
            started_at = time.monotonic()
            if self._settings.enable_audio:
                device = SystemAudioDeviceSelector().select(self._settings.audio_device)
                if device is None:
                    self._logger.warning(
                        "No system-audio loopback device found; microphone capture is disabled."
                    )
                else:
                    capture_device = device
                    self._logger.info("Capturing system audio from: %s", device.name)
                    audio_output = AudioOutput(
                        sample_rate=device.sample_rate,
                        block_size=self._settings.block_size,
                        logger=self._logger,
                    )
                    def process_audio_block(samples: np.ndarray) -> None:
                        if recognition_service is not None:
                            recognition_service.submit_samples(samples)
                        if audio_output is not None:
                            audio_output.push(samples)

                    audio_input = AudioInput(
                        analyzer=AudioAnalyzer(sample_rate=device.sample_rate),
                        on_frame=self._scene_manager.update_audio,
                        sample_rate=device.sample_rate,
                        block_size=self._settings.block_size,
                        device=device.name,
                        channels=device.channels,
                        on_samples=process_audio_block,
                        logger=self._logger,
                    )
                    audio_input.start()
            select_recognition_mode(recognition_settings.mode)
            self._logger.info("MusicScope started. Close the window to quit.")
            while not window.should_close:
                window.poll_events()
                keys = window.consume_pressed_keys()
                self._handle_oscillation_menu_shortcuts(keys, oscillation_menu)
                state = self._scene_manager.state
                width, height = window.framebuffer_size
                context.viewport = (0, 0, width, height)
                elapsed = time.monotonic() - started_at
                crt_renderer.render(state.energy, elapsed)
                oscilloscope_renderer.render(state, elapsed)
                artwork_renderer.render(state, elapsed)
                track_info_renderer.render(state)
                visual_lines, audio_lines = oscillation_menu.columns()
                settings_menu_renderer.render(oscillation_menu.visible, visual_lines, audio_lines)
                window.present()
        finally:
            if audio_input is not None:
                audio_input.stop()
            if audio_output is not None:
                audio_output.stop()
            if recognition_service is not None:
                recognition_service.stop()
            if cd_metadata_service is not None:
                cd_metadata_service.stop()
            window.close()

    def _apply_identification(self, result: IdentificationResult) -> None:
        """Publish a recognized track without coupling the renderer to AudD."""
        artwork_path = str(result.artwork.path) if result.artwork is not None else None
        self._scene_manager.set_track(result.track.title, result.track.artist, artwork_path)
        self._logger.info("Recognized: %s — %s", result.track.artist, result.track.title)
        if artwork_path is None:
            self._logger.info("No cover found; keeping the selected centre visual.")

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
    parser.add_argument(
        "--recognition-mode",
        choices=tuple(RecognitionMode),
        default=RecognitionMode.AUDD,
        help="metadata source: audd, local-cd, or off",
    )
    parser.add_argument(
        "--cd-device",
        help="optical-drive path used by local-cd mode (for example /dev/sr0)",
    )
    args = parser.parse_args()
    settings = AppSettings(
        width=args.width,
        height=args.height,
        fullscreen=args.fullscreen,
        enable_audio=not args.no_audio,
        audio_device=args.audio_device,
        cd_device=args.cd_device,
        recognition_mode=RecognitionMode(args.recognition_mode),
        logo=args.logo,
    )
    MusicScopeApp(settings).run()
