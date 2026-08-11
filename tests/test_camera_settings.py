"""Tests for the camera-background runtime setting."""

from musicscope.renderer.camera_settings import BackgroundMode, CameraSettings


def test_camera_background_setting_cycles_between_crt_and_camera() -> None:
    settings = CameraSettings()

    settings.cycle(1)

    assert settings.mode is BackgroundMode.CAMERA
    assert settings.enabled

    settings.cycle(1)

    assert settings.mode is BackgroundMode.CRT
    assert not settings.enabled


def test_camera_background_setting_cycles_camera_inputs() -> None:
    settings = CameraSettings(device_index=0)

    settings.cycle_device(-1)

    assert settings.device_index == 7
