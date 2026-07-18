"""Tests for runtime oscilloscope settings controls."""

from musicscope.audio.output import AudioOutputDevice
from musicscope.audio.output_settings import AudioOutputSettings
from musicscope.config import RecognitionMode
from musicscope.core.oscillation_menu import OscillationMenu
from musicscope.core.recognition_settings import RecognitionSettings
from musicscope.renderer.color_settings import ColorMode, ColorSettings
from musicscope.renderer.oscillation_settings import OscillationSettings


def test_menu_toggles_and_formats_the_selected_setting() -> None:
    menu = OscillationMenu(OscillationSettings(), ColorSettings())

    menu.toggle()

    assert menu.visible
    assert menu.lines()[0].startswith("> AMPLITUDE")


def test_menu_adjusts_the_selected_setting() -> None:
    settings = OscillationSettings()
    menu = OscillationMenu(settings, ColorSettings())

    menu.adjust_selected(1)

    assert settings.amplitude == 0.52


def test_menu_selection_wraps() -> None:
    menu = OscillationMenu(OscillationSettings(), ColorSettings())

    menu.move_selection(-1)

    assert menu.lines()[-1].startswith("> RECOGNITION")


def test_menu_cycles_the_color_mode() -> None:
    colors = ColorSettings(mode=ColorMode.NEON_GREEN)
    menu = OscillationMenu(OscillationSettings(), colors)
    menu.move_selection(-3)

    menu.adjust_selected(1)

    assert colors.mode is ColorMode.COVER_NEON


def test_menu_selects_an_audio_output() -> None:
    selected: list[AudioOutputDevice | None] = []
    output = AudioOutputSettings((AudioOutputDevice("Hi-Fi Jack", 2),))
    menu = OscillationMenu(
        OscillationSettings(),
        ColorSettings(),
        output_settings=output,
        on_output_change=selected.append,
    )
    menu.move_selection(-2)

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
    menu.move_selection(-1)

    menu.adjust_selected(1)

    assert recognition.mode is RecognitionMode.LOCAL_CD
    assert selected == [RecognitionMode.LOCAL_CD]


def test_menu_groups_visual_and_audio_options_into_separate_columns() -> None:
    visual, audio = OscillationMenu(OscillationSettings(), ColorSettings()).columns()

    assert len(visual) == 4
    assert "AMPLITUDE" in visual[0]
    assert len(audio) == 2
    assert "OUTPUT" in audio[0]
