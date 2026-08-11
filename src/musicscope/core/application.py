"""Application composition root and CLI."""

import argparse
import logging
import sys
import time
from collections.abc import Callable
from pathlib import Path

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
    CdEjector,
    CdPlayer,
    LocalArtworkService,
    LocalPlaylist,
    LocalPlaylistPlayer,
    SystemAudioDeviceSelector,
    WindowsLoopbackInput,
)
from musicscope.camera import CameraCapture, OpenCvCameraSource
from musicscope.config import LOGO_NAMES, AppSettings, RecognitionMode
from musicscope.config.environment import load_project_environment
from musicscope.core.oscillation_menu import OscillationMenu
from musicscope.core.playlist_menu import PlaylistAction, PlaylistMenu
from musicscope.core.recognition_settings import RecognitionSettings
from musicscope.graphics import create_context
from musicscope.lyrics import (
    FallbackLyricsSource,
    LrclibLyricsSource,
    LyricsOvhSource,
    LyricsService,
    display_at,
)
from musicscope.recognition import RecognitionEngine
from musicscope.recognition.cd import MusicBrainzCdLookup
from musicscope.recognition.cd_service import CdMetadataService
from musicscope.recognition.configuration import configured_audd_provider
from musicscope.recognition.models import RecognizedTrack
from musicscope.recognition.service import RecognitionService
from musicscope.recognition.workflow import IdentificationResult, IdentificationWorkflow
from musicscope.renderer import (
    ArtworkRenderer,
    BackgroundMode,
    CameraBackgroundRenderer,
    CameraSettings,
    ColorSettings,
    CrtRenderer,
    LyricsRenderer,
    OscillationSettings,
    OscilloscopeRenderer,
    PlaybackProgressRenderer,
    PlaylistMenuRenderer,
    SettingsMenuRenderer,
    TrackInfoRenderer,
    TrackInfoSettings,
)
from musicscope.scene import SceneManager
from musicscope.utils.logging import configure_logging
from musicscope.window import GlfwWindow, KeyPress, MouseButtonEvent


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
        audio_input: AudioInput | WindowsLoopbackInput | None = None
        audio_output: AudioOutput | None = None
        recognition_service: RecognitionService | None = None
        cd_metadata_service: CdMetadataService | None = None
        cd_player: CdPlayer | None = None
        cd_tracks: tuple[RecognizedTrack, ...] = ()
        cd_artwork_path: str | None = None
        cd_lyrics: tuple[tuple[float, str], ...] = ()
        cd_position = 0.0
        cd_duration = 0.0
        playback_progress_visible = False
        lyrics_service: LyricsService | None = None
        local_playlist = LocalPlaylist()
        local_player: LocalPlaylistPlayer | None = None
        local_artwork_service: LocalArtworkService | None = None
        local_lyrics: tuple[tuple[float, str], ...] = ()
        local_lyrics_service: LyricsService | None = None
        local_current_path: Path | None = None
        local_playback_started_at: float | None = None
        local_position = 0.0
        local_duration = 0.0
        camera_capture: CameraCapture | None = None
        cd_ejector = CdEjector(device=self._settings.cd_device, logger=self._logger)
        capture_device = None
        try:
            window.open()
            context = create_context()
            oscillation_settings = OscillationSettings()
            color_settings = ColorSettings()
            track_info_settings = TrackInfoSettings()
            camera_settings = CameraSettings()
            crt_renderer = CrtRenderer(context, color_settings=color_settings)
            oscilloscope_renderer = OscilloscopeRenderer(
                context,
                settings=oscillation_settings,
                color_settings=color_settings,
                track_info_settings=track_info_settings,
            )
            artwork_renderer = ArtworkRenderer(
                context,
                logo=self._settings.logo,
                color_settings=color_settings,
                track_info_settings=track_info_settings,
            )
            camera_renderer = CameraBackgroundRenderer(context)
            track_info_renderer = TrackInfoRenderer(
                context,
                color_settings=color_settings,
                settings=track_info_settings,
            )
            lyrics_renderer = LyricsRenderer(context, color_settings, track_info_settings)
            playback_progress_renderer = PlaybackProgressRenderer(context, color_settings)
            settings_menu_renderer = SettingsMenuRenderer(context, color_settings=color_settings)
            playlist_menu_renderer = PlaylistMenuRenderer(context, color_settings=color_settings)
            output_selector = AudioOutputDeviceSelector()
            output_settings = AudioOutputSettings(
                output_selector.available(),
                default_device=output_selector.default_output(),
            )
            recognition_settings = RecognitionSettings(self._settings.recognition_mode)

            def select_audio_output(device: AudioOutputDevice | None) -> None:
                if audio_output is None:
                    self._logger.warning("Audio output cannot start without an input source.")
                    return
                audio_output.select(device)

            def select_recognition_mode(mode: RecognitionMode) -> None:
                nonlocal cd_artwork_path, cd_lyrics, cd_metadata_service, cd_player
                nonlocal cd_tracks, lyrics_service, local_artwork_service, local_current_path
                nonlocal local_lyrics_service, local_player
                nonlocal recognition_service
                nonlocal cd_duration, cd_position
                if recognition_service is not None:
                    recognition_service.stop()
                    recognition_service = None
                if cd_metadata_service is not None:
                    cd_metadata_service.stop()
                    cd_metadata_service = None
                if cd_player is not None:
                    cd_player.stop()
                    cd_player = None
                if local_player is not None:
                    local_player.stop()
                if local_artwork_service is not None:
                    local_artwork_service.cancel()
                if local_lyrics_service is not None:
                    local_lyrics_service.cancel()
                local_current_path = None
                cd_tracks = ()
                cd_artwork_path = None
                cd_lyrics = ()
                cd_position = 0.0
                cd_duration = 0.0
                self._scene_manager.set_lyric_line(None)
                if mode is RecognitionMode.OFF:
                    recognition_settings.set_status("OFF")
                    self._logger.info("Music recognition disabled.")
                    return
                if mode is RecognitionMode.LOCAL_CD:
                    recognition_settings.set_status("CD")
                    speaker_output = output_settings.select_system_default()
                    if speaker_output is not None:
                        select_audio_output(speaker_output)
                        self._logger.info("CD playback output selected: %s", speaker_output.name)
                    else:
                        self._logger.warning(
                            "No physical audio output is available for CD playback."
                        )

                    def set_lyrics(lines: tuple[tuple[float, str], ...]) -> None:
                        nonlocal cd_lyrics
                        cd_lyrics = lines
                        self._scene_manager.set_lyric_line(None)

                    def update_cd_track(number: int) -> None:
                        nonlocal cd_position, cd_duration
                        cd_position = 0.0
                        cd_duration = 0.0
                        self._apply_cd_track(number, cd_tracks, cd_artwork_path)
                        if lyrics_service is not None and number <= len(cd_tracks):
                            lyrics_service.load(cd_tracks[number - 1])

                    def update_lyric_time(seconds: float) -> None:
                        nonlocal cd_position
                        cd_position = seconds
                        display = display_at(
                            cd_lyrics,
                            seconds,
                            entry_effect=track_info_settings.lyric_entry_effect.value,
                        )
                        self._scene_manager.set_lyric_line(
                            display.line,
                            display.opacity,
                            display.morph,
                        )

                    def update_cd_duration(seconds: float) -> None:
                        nonlocal cd_duration
                        cd_duration = seconds

                    lyrics_service = LyricsService(
                        FallbackLyricsSource(
                            (LrclibLyricsSource(), LyricsOvhSource()),
                            logger=self._logger,
                        ),
                        set_lyrics,
                        logger=self._logger,
                    )
                    cd_player = CdPlayer(
                        device=self._settings.cd_device,
                        audio_device=capture_device.name if capture_device is not None else None,
                        on_track_change=update_cd_track,
                        on_playback_time=update_lyric_time,
                        on_duration=update_cd_duration,
                        logger=self._logger,
                    )

                    def apply_local_cd_identification(result: IdentificationResult) -> None:
                        """Start playback only after its cover and lyrics are resolved."""
                        nonlocal cd_artwork_path, cd_tracks
                        cd_tracks = result.album_tracks
                        cd_artwork_path = (
                            str(result.artwork.path) if result.artwork is not None else None
                        )
                        self._apply_identification(result)

                        def start_playback(
                            lyrics: tuple[tuple[float, str], ...],
                        ) -> None:
                            if (
                                recognition_settings.mode is RecognitionMode.LOCAL_CD
                                and cd_player is not None
                            ):
                                self._logger.info(
                                    "CD visual assets ready (%s); starting playback.",
                                    "timed lyrics loaded" if lyrics else "no timed lyrics",
                                )
                                cd_player.start()

                        if lyrics_service is not None:
                            self._logger.info("Cover ready; waiting for timed lyric lookup.")
                            lyrics_service.load(result.track, on_ready=start_playback)
                        else:
                            start_playback(())

                    cd_metadata_service = CdMetadataService(
                        lookup=MusicBrainzCdLookup(),
                        artwork_pipeline=ArtworkPipeline.default(),
                        on_identification=apply_local_cd_identification,
                        device=self._settings.cd_device,
                        logger=self._logger,
                    )
                    cd_metadata_service.start()
                    self._logger.info("Local CD metadata recognition enabled (AudD is disabled).")
                    return
                if capture_device is None:
                    recognition_settings.set_status("NO INPUT")
                    self._logger.warning("AudD needs an active audio input source.")
                    return
                provider = configured_audd_provider(self._logger)
                if provider is None:
                    recognition_settings.set_status("NO TOKEN")
                    return
                recognition_service = RecognitionService(
                    workflow=IdentificationWorkflow(
                        RecognitionEngine(provider),
                        ArtworkPipeline.default(),
                    ),
                    sample_rate=capture_device.sample_rate,
                    on_identification=self._apply_identification,
                    logger=self._logger,
                    on_status=recognition_settings.set_status,
                )
                recognition_service.start()

            def select_camera_background(enabled: bool) -> None:
                nonlocal camera_capture
                if enabled:
                    if camera_capture is None:
                        camera_capture = CameraCapture(
                            OpenCvCameraSource(camera_settings.device_index, logger=self._logger)
                        )
                    if not camera_capture.start():
                        camera_settings.mode = BackgroundMode.CRT
                elif camera_capture is not None:
                    camera_capture.stop()

            def select_camera_device(_index: int) -> None:
                nonlocal camera_capture
                if not camera_settings.enabled:
                    return
                if camera_capture is not None:
                    camera_capture.stop()
                    camera_capture = None
                select_camera_background(True)

            oscillation_menu = OscillationMenu(
                oscillation_settings,
                color_settings,
                track_info_settings=track_info_settings,
                output_settings=output_settings,
                on_output_change=select_audio_output,
                recognition_settings=recognition_settings,
                on_recognition_change=select_recognition_mode,
                camera_settings=camera_settings,
                on_background_change=select_camera_background,
                on_camera_device_change=select_camera_device,
            )
            playlist_menu = PlaylistMenu()
            started_at = time.monotonic()
            def process_audio_block(samples: np.ndarray) -> None:
                if recognition_service is not None:
                    recognition_service.submit_samples(samples)
                if audio_output is not None:
                    audio_output.push(samples)

            if self._settings.enable_audio:
                device = SystemAudioDeviceSelector().select(self._settings.audio_device)
                if device is None:
                    if sys.platform == "win32":
                        self._logger.info(
                            "Capturing default Windows speaker through WASAPI loopback."
                        )
                        audio_input = WindowsLoopbackInput(
                            analyzer=AudioAnalyzer(sample_rate=self._settings.sample_rate),
                            on_frame=self._scene_manager.update_audio,
                            sample_rate=self._settings.sample_rate,
                            block_size=self._settings.block_size,
                            on_samples=process_audio_block,
                            logger=self._logger,
                        )
                        audio_input.start()
                    else:
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

            def update_local_track(number: int) -> None:
                nonlocal local_current_path, local_playback_started_at
                nonlocal local_position, local_duration
                local_playback_started_at = time.monotonic()
                local_position = 0.0
                local_duration = 0.0
                item = local_playlist.item_at(number)
                if item is None:
                    return
                local_current_path = item.path
                self._scene_manager.set_track(
                    item.track.title,
                    item.track.artist,
                    artwork_path=str(item.artwork_path) if item.artwork_path is not None else None,
                    track_number=item.track.track_number,
                )
                self._scene_manager.set_lyric_line(None)
                if local_artwork_service is not None:
                    local_artwork_service.load(number)
                if local_lyrics_service is not None:
                    local_lyrics_service.load(item.track)
                self._logger.info(
                    "Local playlist track: %s — %s", item.track.artist, item.track.title
                )

            def update_local_artwork(number: int, artwork_path: str | None) -> None:
                item = local_playlist.item_at(number)
                if item is None:
                    return
                self._scene_manager.set_track(
                    item.track.title,
                    item.track.artist,
                    artwork_path=artwork_path,
                    track_number=item.track.track_number,
                )

            def set_local_lyrics(lines: tuple[tuple[float, str], ...]) -> None:
                nonlocal local_lyrics
                local_lyrics = lines
                self._scene_manager.set_lyric_line(None)
                if not lines:
                    self._scene_manager.mark_lyrics_unavailable()

            def update_local_lyric_time(seconds: float) -> None:
                nonlocal local_position
                local_position = seconds
                display = display_at(
                    local_lyrics,
                    seconds,
                    entry_effect=track_info_settings.lyric_entry_effect.value,
                )
                self._scene_manager.set_lyric_line(
                    display.line,
                    display.opacity,
                    display.morph,
                )

            def update_local_duration(seconds: float) -> None:
                nonlocal local_duration
                local_duration = seconds

            local_artwork_service = LocalArtworkService(
                local_playlist,
                ArtworkPipeline.default(),
                update_local_artwork,
                logger=self._logger,
            )
            local_lyrics_service = LyricsService(
                FallbackLyricsSource(
                    (LrclibLyricsSource(), LyricsOvhSource()),
                    logger=self._logger,
                ),
                set_local_lyrics,
                logger=self._logger,
            )

            local_player = LocalPlaylistPlayer(
                audio_device=capture_device.name if capture_device is not None else None,
                audio_device_resolver=CdPlayer()._resolve_mpv_audio_device,
                on_track_change=update_local_track,
                on_playback_time=update_local_lyric_time,
                on_duration=update_local_duration,
                logger=self._logger,
            )
            dragging_playlist_index: int | None = None
            dragging_playback = False
            last_playback_seek_at = 0.0

            def play_local_playlist(start_at: int = 1) -> None:
                nonlocal local_playback_started_at
                if local_player is None or not local_playlist.paths:
                    return
                local_player.play(local_playlist.paths, start_at=start_at)
                local_playback_started_at = time.monotonic()
                update_local_track(start_at)

            def clear_local_playlist() -> None:
                nonlocal local_current_path, local_playback_started_at
                had_tracks = local_playlist.size > 0
                if local_player is not None:
                    local_player.stop()
                if local_artwork_service is not None:
                    local_artwork_service.cancel()
                if local_lyrics_service is not None:
                    local_lyrics_service.cancel()
                local_playlist.clear()
                local_current_path = None
                local_playback_started_at = None
                if had_tracks:
                    self._scene_manager.clear_track()
                self._logger.info("Local playlist cleared.")

            def handle_playlist_mouse(event: MouseButtonEvent) -> None:
                nonlocal dragging_playlist_index
                window_width, window_height = window.window_size
                if event.action == glfw.PRESS:
                    hit = playlist_menu.action_at(
                        event.x,
                        event.y,
                        window_width,
                        window_height,
                        local_playlist.size,
                    )
                    if hit is None:
                        return
                    action, index = hit
                    if action is PlaylistAction.CLEAR:
                        clear_local_playlist()
                    elif action is PlaylistAction.DELETE and index is not None:
                        removed = local_playlist.remove(index)
                        if removed is None:
                            return
                        current_index = (
                            local_playlist.index_of_path(local_current_path)
                            if local_current_path is not None
                            else None
                        )
                        if local_playlist.size:
                            play_local_playlist(current_index or min(index, local_playlist.size))
                        else:
                            clear_local_playlist()
                    elif action is PlaylistAction.TRACK:
                        dragging_playlist_index = index
                    return
                if event.action != glfw.RELEASE or dragging_playlist_index is None:
                    return
                destination = playlist_menu.track_index_at(
                    event.x,
                    event.y,
                    window_width,
                    window_height,
                    local_playlist.size,
                )
                source = dragging_playlist_index
                dragging_playlist_index = None
                if destination is None:
                    return
                if source == destination:
                    play_local_playlist(source)
                    self._logger.info("Selected local playlist track %s.", source)
                    return
                if local_playlist.move(source, destination):
                    current_index = (
                        local_playlist.index_of_path(local_current_path)
                        if local_current_path is not None
                        else None
                    )
                    play_local_playlist(current_index or 1)
                    self._logger.info("Local playlist reordered.")
            self._logger.info("MusicScope started. Close the window to quit.")
            while not window.should_close:
                window.poll_events()
                dropped_files = window.consume_dropped_files()
                if dropped_files:
                    added_tracks = local_playlist.add(dropped_files)
                    if added_tracks:
                        recognition_settings.mode = RecognitionMode.OFF
                        select_recognition_mode(RecognitionMode.OFF)
                        play_local_playlist()
                        self._logger.info(
                            "Added %s local track(s); playlist contains %s track(s).",
                            len(added_tracks),
                            len(local_playlist.paths),
                        )
                    else:
                        self._logger.warning(
                            "No supported audio files were dropped. "
                            "Supported: MP3, M4A, FLAC, WAV, OGG, OPUS, AAC, AIFF."
                        )
                mouse_events = window.consume_mouse_button_events()
                for mouse_event in mouse_events:
                    if playlist_menu.visible:
                        handle_playlist_mouse(mouse_event)
                keys = window.consume_pressed_keys()
                playlist_navigation_keys: list[KeyPress] = []
                for press in keys:
                    if press.key == glfw.KEY_SPACE:
                        playback_progress_visible = not playback_progress_visible
                        self._logger.info(
                            "Playback progress %s.",
                            "shown" if playback_progress_visible else "hidden",
                        )
                    if press.key == glfw.KEY_P:
                        playlist_menu.toggle()
                        self._logger.info(
                            "Playlist menu %s.", "opened" if playlist_menu.visible else "closed"
                        )
                    if playlist_menu.visible and press.key == glfw.KEY_UP:
                        playlist_menu.scroll(-1, local_playlist.size)
                        playlist_navigation_keys.append(press)
                    if playlist_menu.visible and press.key == glfw.KEY_DOWN:
                        playlist_menu.scroll(1, local_playlist.size)
                        playlist_navigation_keys.append(press)
                shortcut_keys = tuple(
                    press for press in keys if press not in playlist_navigation_keys
                )
                self._handle_shortcuts(
                    shortcut_keys,
                    oscillation_menu,
                    on_eject=cd_ejector.eject,
                    on_stop_cd=cd_player.stop if cd_player is not None else None,
                )
                if playback_progress_visible and not playlist_menu.visible:
                    window_width, window_height = window.window_size

                    def seek_playback(
                        cursor_x: float,
                        width: int = window_width,
                        height: int = window_height,
                        force: bool = False,
                    ) -> None:
                        nonlocal last_playback_seek_at
                        now = time.monotonic()
                        if not force and now - last_playback_seek_at < 0.10:
                            return
                        fraction = PlaybackProgressRenderer.fraction_from_cursor(
                            cursor_x,
                            width,
                            width / height if height else 1.0,
                        )
                        last_playback_seek_at = now
                        if local_player is not None and local_player.is_playing:
                            if not local_player.seek_to_fraction(fraction):
                                self._logger.warning("Local playback seeking is not ready yet.")
                        elif cd_player is not None and not cd_player.seek_to_fraction(fraction):
                            self._logger.warning("CD seeking is not ready yet.")

                    for mouse_event in mouse_events:
                        if mouse_event.action == glfw.PRESS:
                            dragging_playback = True
                            seek_playback(mouse_event.x, force=True)
                        elif mouse_event.action == glfw.RELEASE:
                            dragging_playback = False
                            seek_playback(mouse_event.x, force=True)
                    if dragging_playback:
                        cursor_x, _cursor_y = window.cursor_position
                        seek_playback(cursor_x)
                if (
                    sys.platform == "win32"
                    and local_player is not None
                    and local_player.is_playing
                    and local_playback_started_at is not None
                ):
                    update_local_lyric_time(time.monotonic() - local_playback_started_at)
                state = self._scene_manager.state
                width, height = window.framebuffer_size
                context.viewport = (0, 0, width, height)
                elapsed = time.monotonic() - started_at
                camera_frame = (
                    camera_capture.frame if camera_settings.enabled and camera_capture else None
                )
                if camera_frame is not None:
                    camera_renderer.render(camera_frame, (width, height))
                    crt_renderer.render(state.energy, elapsed, overlay=True)
                else:
                    crt_renderer.render(state.energy, elapsed)
                oscilloscope_renderer.render(state, elapsed)
                if not camera_settings.enabled:
                    artwork_renderer.render(state, elapsed)
                track_info_renderer.render(state)
                lyrics_renderer.render(state, elapsed)
                is_local_playback = local_player is not None and local_player.is_playing
                playback_progress_renderer.render(
                    playback_progress_visible,
                    local_position if is_local_playback else cd_position,
                    local_duration if is_local_playback else cd_duration,
                )
                visual_lines, audio_lines = oscillation_menu.columns()
                settings_menu_renderer.render(oscillation_menu.visible, visual_lines, audio_lines)
                playlist_menu_renderer.render(
                    playlist_menu.visible,
                    local_playlist,
                    local_playlist.index_of_path(local_current_path)
                    if local_current_path is not None
                    else None,
                    dragging_playlist_index,
                    playlist_menu.max_visible_tracks,
                    playlist_menu.offset,
                )
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
            if cd_player is not None:
                cd_player.stop()
            if local_player is not None:
                local_player.stop()
            if local_artwork_service is not None:
                local_artwork_service.cancel()
            if camera_capture is not None:
                camera_capture.stop()
            window.close()

    def _apply_identification(self, result: IdentificationResult) -> None:
        """Publish a recognized track without coupling the renderer to AudD."""
        artwork_path = str(result.artwork.path) if result.artwork is not None else None
        self._scene_manager.set_track(
            result.track.title,
            result.track.artist,
            artwork_path,
            track_number=result.track.track_number,
        )
        self._logger.info("Recognized: %s — %s", result.track.artist, result.track.title)
        if artwork_path is not None:
            self._logger.info("Displaying cover from cache: %s", artwork_path)
        else:
            self._logger.info("No cover found; keeping the selected centre visual.")

    def _apply_cd_track(
        self,
        number: int,
        tracks: tuple[RecognizedTrack, ...],
        artwork_path: str | None,
    ) -> None:
        """Update the title when mpv advances through the locally loaded CD."""
        if number > len(tracks):
            return
        track = tracks[number - 1]
        self._scene_manager.set_track(
            track.title,
            track.artist,
            artwork_path,
            track_number=track.track_number,
        )
        self._logger.info("CD track: %s — %s", track.artist, track.title)

    def _handle_shortcuts(
        self,
        keys: tuple[KeyPress, ...],
        menu: OscillationMenu,
        on_eject: Callable[[], bool],
        on_stop_cd: Callable[[], None] | None,
    ) -> None:
        """Route application shortcuts without coupling GLFW input to renderers."""
        eject_modifier = glfw.MOD_SUPER if sys.platform == "darwin" else glfw.MOD_CONTROL
        for press in keys:
            key = press.key
            if key == glfw.KEY_E and press.modifiers & eject_modifier:
                if on_stop_cd is not None:
                    on_stop_cd()
                on_eject()
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
    parser.add_argument("--logo", choices=LOGO_NAMES, default="musicscope")
    parser.add_argument(
        "--recognition-mode",
        choices=tuple(RecognitionMode),
        default=RecognitionMode.LOCAL_CD,
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
