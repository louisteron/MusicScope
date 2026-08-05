"""Owns the active scene's visual state."""

from threading import Lock

from musicscope.audio.analyzer import AudioFrame
from musicscope.scene.model import VisualState


class SceneManager:
    """Translate audio frames into a state usable by a renderer."""

    def __init__(self) -> None:
        self._state = VisualState()
        self._lock = Lock()

    @property
    def state(self) -> VisualState:
        """Return the most recently calculated visual state."""
        with self._lock:
            return self._state

    def update_audio(self, frame: AudioFrame) -> None:
        """Apply fast attack and slow release for phosphor-like signal persistence."""
        with self._lock:
            energy = self._smooth_energy(frame.volume)
            previous = self._state.spectrum
            spectrum = (
                tuple(
                    old * 0.65 + new * 0.35
                    for old, new in zip(previous, frame.spectrum, strict=True)
                )
                if previous
                else frame.spectrum
            )
            waveform = self._smooth_waveform(frame.waveform)
            self._state = VisualState(
                energy=energy,
                bass_energy=self._smooth_bass(frame.bass_energy),
                spectrum=spectrum,
                waveform=waveform,
                track_title=self._state.track_title,
                artist_name=self._state.artist_name,
                track_number=self._state.track_number,
                lyric_line=self._state.lyric_line,
                lyric_opacity=self._state.lyric_opacity,
                lyric_morph=self._state.lyric_morph,
                lyrics_seen=self._state.lyrics_seen,
                artwork_path=self._state.artwork_path,
            )

    def _smooth_energy(self, volume: float) -> float:
        if volume >= self._state.energy:
            return self._state.energy * 0.55 + volume * 0.45
        return self._state.energy * 0.985 + volume * 0.015

    def _smooth_bass(self, bass_energy: float) -> float:
        """Keep bass hits punchy while allowing their phosphor tail to fade."""
        if bass_energy >= self._state.bass_energy:
            return self._state.bass_energy * 0.35 + bass_energy * 0.65
        return self._state.bass_energy * 0.82 + bass_energy * 0.18

    def _smooth_waveform(self, waveform: tuple[float, ...]) -> tuple[float, ...]:
        previous = self._state.waveform
        if not previous:
            return waveform
        if len(previous) != len(waveform):
            return waveform
        incoming_weight = 0.70 if self._state.energy > 0.002 else 0.035
        return tuple(
            old * (1.0 - incoming_weight) + new * incoming_weight
            for old, new in zip(previous, waveform, strict=True)
        )

    def set_track(
        self,
        title: str,
        artist: str,
        artwork_path: str | None,
        track_number: int | None = None,
    ) -> None:
        """Publish recognized metadata as renderer-neutral scene state."""
        with self._lock:
            self._state = VisualState(
                energy=self._state.energy,
                bass_energy=self._state.bass_energy,
                spectrum=self._state.spectrum,
                waveform=self._state.waveform,
                track_title=title,
                artist_name=artist,
                track_number=track_number,
                lyric_line=None,
                lyric_opacity=1.0,
                lyric_morph=1.0,
                lyrics_seen=False,
                artwork_path=artwork_path,
            )

    def set_lyric_line(
        self,
        line: str | None,
        opacity: float = 1.0,
        morph: float = 1.0,
    ) -> None:
        """Publish the currently active timed lyric line."""
        with self._lock:
            self._state = VisualState(
                energy=self._state.energy,
                bass_energy=self._state.bass_energy,
                spectrum=self._state.spectrum,
                waveform=self._state.waveform,
                track_title=self._state.track_title,
                artist_name=self._state.artist_name,
                track_number=self._state.track_number,
                lyric_line=line,
                lyric_opacity=max(0.0, min(1.0, opacity)),
                lyric_morph=max(0.0, min(1.0, morph)),
                lyrics_seen=self._state.lyrics_seen or line is not None,
                artwork_path=self._state.artwork_path,
            )

    def mark_lyrics_unavailable(self) -> None:
        """Keep lyrics mode from hiding the normal scope for local files."""
        with self._lock:
            self._state = VisualState(
                energy=self._state.energy,
                bass_energy=self._state.bass_energy,
                spectrum=self._state.spectrum,
                waveform=self._state.waveform,
                track_title=self._state.track_title,
                artist_name=self._state.artist_name,
                track_number=self._state.track_number,
                lyric_line=None,
                lyric_opacity=1.0,
                lyric_morph=1.0,
                lyrics_seen=True,
                artwork_path=self._state.artwork_path,
            )

    def clear_track(self) -> None:
        """Remove track metadata and artwork after clearing a local playlist."""
        with self._lock:
            self._state = VisualState(
                energy=self._state.energy,
                bass_energy=self._state.bass_energy,
                spectrum=self._state.spectrum,
                waveform=self._state.waveform,
            )
