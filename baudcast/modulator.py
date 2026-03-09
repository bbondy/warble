"""Audio waveform generation for Baudcast transmissions."""

from __future__ import annotations

import math
from collections.abc import Sequence

from baudcast.config import BaudcastConfig, DEFAULT_CONFIG
from baudcast.framing import build_file_frames, frame_to_bits


def generate_tone(
    frequency: float,
    config: BaudcastConfig = DEFAULT_CONFIG,
    *,
    amplitude: float | None = None,
) -> list[float]:
    """Generate one symbol of a sine wave for the requested frequency."""
    level = config.amplitude if amplitude is None else amplitude
    samples: list[float] = []
    for index in range(config.samples_per_symbol):
        angle = 2.0 * math.pi * frequency * (index / config.sample_rate)
        samples.append(level * math.sin(angle))
    return samples


def bits_to_samples(
    bits: Sequence[int],
    config: BaudcastConfig = DEFAULT_CONFIG,
    *,
    amplitude: float | None = None,
) -> list[float]:
    """Convert a bit sequence into concatenated audio samples."""
    output: list[float] = []
    zero_symbol = generate_tone(config.freq0, config, amplitude=amplitude)
    one_symbol = generate_tone(config.freq1, config, amplitude=amplitude)
    for bit in bits:
        output.extend(one_symbol if int(bit) else zero_symbol)
    return output


def frames_to_samples(
    frames: Sequence[bytes],
    config: BaudcastConfig = DEFAULT_CONFIG,
    *,
    amplitude: float | None = None,
) -> list[float]:
    """Convert a frame sequence into audio samples."""
    bits: list[int] = []
    for frame in frames:
        bits.extend(frame_to_bits(frame))
    return bits_to_samples(bits, config, amplitude=amplitude)


def file_bytes_to_samples(
    data: bytes,
    config: BaudcastConfig = DEFAULT_CONFIG,
    *,
    amplitude: float | None = None,
) -> list[float]:
    """Convert file bytes into the audio needed for transmission."""
    return frames_to_samples(build_file_frames(data, config), config, amplitude=amplitude)
