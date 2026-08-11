"""Tests for runtime oscilloscope settings controls."""

from musicscope.audio.output import AudioOutputDevice
from musicscope.audio.output_settings import AudioOutputSettings
from musicscope.config import RecognitionMode
from musicscope.core.oscillation_menu import OscillationMenu
from musicscope.core.recognition_settings import RecognitionSettings
from musicscope.renderer.camera_settings import CameraSettings
from musicscope.renderer.color_settings import ColorMode, ColorSettings, PhosphorColor
from musicscope.renderer.oscillation_settings import OscillationSettings
from musicscope.renderer.track_info_settings import LyricEntryEffect, TrackInfoSettings


def test_menu_toggles_and_formats_the_selected_setting() -> None:
    menu = OscillationMenu(OscillationSettings(), ColorSettings())

    menu.toggle()

    assert menu.visible
    assert menu.lines()[0].startswith("> AMPLITUDE")


def test_lyrics_visual_starts_enabled_without_a_text_fade() -> None:
    settings = TrackInfoSettings()

    assert settings.lyrics_wave
    assert settings.lyric_entry_effect.value == "NO FADE"


def test_menu_adjusts_the_selected_setting() -> None:
    settings = OscillationSettings()
    menu = OscillationMenu(settings, ColorSettings())

    menu.adjust_selected(1)

    assert settings.amplitude == 0.52


def test_menu_selection_wraps() -> None:
    menu = OscillationMenu(OscillationSettings(), ColorSettings())

    menu.move_selection(-1)

    assert menu.lines()[-1].startswith("> CAMERA INPUT  1")


def test_menu_cycles_the_color_mode() -> None:
    colors = ColorSettings(mode=ColorMode.NEON_GREEN)
    menu = OscillationMenu(OscillationSettings(), colors)
    menu.move_selection(-10)

    menu.adjust_selected(1)

    assert colors.mode is ColorMode.COVER_NEON


def test_menu_cycles_the_phosphor_color() -> None:
    colors = ColorSettings(phosphor_color=PhosphorColor.GREEN)
    menu = OscillationMenu(OscillationSettings(), colors)
    menu.move_selection(4)

    menu.adjust_selected(1)

    assert colors.phosphor_color is PhosphorColor.WHITE


def test_menu_toggles_track_number_display() -> None:
    track_info = TrackInfoSettings()
    menu = OscillationMenu(OscillationSettings(), ColorSettings(), track_info)
    menu.move_selection(5)

    menu.adjust_selected(1)

    assert track_info.show_track_number


def test_menu_cycles_the_lyric_entry_effect() -> None:
    track_info = TrackInfoSettings(lyric_entry_effect=LyricEntryEffect.FADE)
    menu = OscillationMenu(OscillationSettings(), ColorSettings(), track_info)
    menu.move_selection(8)

    menu.adjust_selected(1)

    assert track_info.lyric_entry_effect.value == "MORPH"

    menu.adjust_selected(1)

    assert track_info.lyric_entry_effect.value == "NO FADE"


def test_menu_toggles_text_wave_distortion() -> None:
    track_info = TrackInfoSettings()
    menu = OscillationMenu(OscillationSettings(), ColorSettings(), track_info)
    menu.move_selection(7)

    menu.adjust_selected(1)

    assert not track_info.lyrics_reactive


def test_menu_selects_an_audio_output() -> None:
    selected: list[AudioOutputDevice | None] = []
    output = AudioOutputSettings((AudioOutputDevice("Hi-Fi Jack", 2),))
    menu = OscillationMenu(
        OscillationSettings(),
        ColorSettings(),
        output_settings=output,
        on_output_change=selected.append,
    )
    menu.move_selection(-3)

    menu.adjust_selected(1)

    assert output.label == "HI-FI JACK"
    assert selected == [AudioOutputDevice("Hi-Fi Jack", 2)]


def test_menu_cycles_the_recognition_mode() -> None:
    selected: list[RecognitionMode] = []
    recognition = RecognitionSettings(RecognitionMode.AUDD)
    menu = OscillationMenu(
        OscillationSettings(),
        ColorSettings(),
        recognition_settings=recognition,
        on_recognition_change=selected.append,
    )
    menu.move_selection(-2)

    menu.adjust_selected(1)

    assert recognition.mode is RecognitionMode.LOCAL_CD
    assert selected == [RecognitionMode.LOCAL_CD]


def test_menu_groups_visual_and_audio_options_into_separate_columns() -> None:
    visual, audio = OscillationMenu(OscillationSettings(), ColorSettings()).columns()

    assert len(visual) == 10
    assert "AMPLITUDE" in visual[0]
    assert len(audio) == 3
    assert "OUTPUT" in audio[0]


def test_menu_changes_the_camera_background() -> None:
    camera = CameraSettings()
    selected: list[bool] = []
    menu = OscillationMenu(
        OscillationSettings(),
        ColorSettings(),
        camera_settings=camera,
        on_background_change=selected.append,
    )
    menu.move_selection(9)

    menu.adjust_selected(1)

    assert camera.enabled
    assert selected == [True]
