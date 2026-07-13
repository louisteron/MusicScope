"""Encoding helpers for audio-recognition clips."""

import wave
from io import BytesIO

import numpy as np


def encode_wav(samples: np.ndarray, sample_rate: int) -> bytes:
    """Encode normalized mono samples as a 16-bit PCM WAV file."""
    mono = np.asarray(samples, dtype=np.float32).reshape(-1)
    pcm = (np.clip(mono, -1.0, 1.0) * 32_767).astype("<i2")
    output = BytesIO()
    with wave.open(output, "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(sample_rate)
        file.writeframes(pcm.tobytes())
    return output.getvalue()
