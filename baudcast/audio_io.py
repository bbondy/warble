"""Audio device wrappers for Baudcast."""

from __future__ import annotations

from typing import Any


def _require_sounddevice() -> Any:
    try:
        import sounddevice as sounddevice
    except ImportError as exc:  # pragma: no cover - depends on local environment
        raise RuntimeError(
            "sounddevice is required for live audio I/O. Install it with "
            "`pip install 'baudcast[audio]'`."
        ) from exc
    return sounddevice


def list_devices() -> list[str]:
    """Return human-readable audio device descriptions."""
    sounddevice = _require_sounddevice()
    devices = sounddevice.query_devices()
    descriptions: list[str] = []
    for index, device in enumerate(devices):
        descriptions.append(
            f"{index}: {device['name']} "
            f"(in={device['max_input_channels']}, out={device['max_output_channels']})"
        )
    return descriptions


def play_samples(
    samples: list[float],
    sample_rate: int,
    *,
    device: int | None = None,
) -> None:
    """Play a mono sample buffer through the selected output device."""
    sounddevice = _require_sounddevice()
    sounddevice.play(samples, samplerate=sample_rate, device=device, blocking=True)


def record_samples(
    duration_seconds: float,
    sample_rate: int,
    *,
    device: int | None = None,
) -> list[float]:
    """Record mono audio for a fixed duration."""
    sounddevice = _require_sounddevice()
    frame_count = max(1, round(duration_seconds * sample_rate))
    recording = sounddevice.rec(
        frame_count,
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
        device=device,
    )
    sounddevice.wait()
    return [float(sample[0]) for sample in recording]
