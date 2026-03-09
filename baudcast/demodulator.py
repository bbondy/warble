"""Tone detection and bit recovery for Baudcast."""

from __future__ import annotations

import math
from collections.abc import Sequence

from baudcast.config import BaudcastConfig, DEFAULT_CONFIG
from baudcast.framing import extract_file_bytes_from_bits, extract_payloads_from_bits


def goertzel_magnitude(samples: Sequence[float], frequency: float, sample_rate: int) -> float:
    """Measure energy at a target frequency using the Goertzel algorithm."""
    sample_count = len(samples)
    if sample_count == 0:
        return 0.0

    normalized_frequency = frequency / sample_rate
    coefficient = 2.0 * math.cos(2.0 * math.pi * normalized_frequency)
    q0 = 0.0
    q1 = 0.0
    q2 = 0.0

    for sample in samples:
        q0 = coefficient * q1 - q2 + sample
        q2 = q1
        q1 = q0

    real = q1 - (q2 * math.cos(2.0 * math.pi * normalized_frequency))
    imag = q2 * math.sin(2.0 * math.pi * normalized_frequency)
    return math.sqrt((real * real) + (imag * imag))


def detect_bit(symbol_samples: Sequence[float], config: BaudcastConfig = DEFAULT_CONFIG) -> int:
    """Detect whether one symbol carries a 0 or a 1."""
    zero_power = goertzel_magnitude(symbol_samples, config.freq0, config.sample_rate)
    one_power = goertzel_magnitude(symbol_samples, config.freq1, config.sample_rate)
    return 1 if one_power >= zero_power else 0


def samples_to_bits(
    samples: Sequence[float],
    config: BaudcastConfig = DEFAULT_CONFIG,
    *,
    offset: int = 0,
) -> list[int]:
    """Slice audio into symbols and detect each bit."""
    step = config.samples_per_symbol
    bits: list[int] = []
    for start in range(offset, len(samples) - step + 1, step):
        bits.append(detect_bit(samples[start:start + step], config))
    return bits


def recover_payloads_from_samples(
    samples: Sequence[float],
    config: BaudcastConfig = DEFAULT_CONFIG,
) -> list[bytes]:
    """Search across possible symbol alignments and recover the most valid frames."""
    best_payloads: list[bytes] = []
    best_score = -1
    max_offset = min(config.samples_per_symbol, len(samples))

    for offset in range(max_offset):
        candidate_bits = samples_to_bits(samples, config, offset=offset)
        payloads = extract_payloads_from_bits(candidate_bits, config)
        if len(payloads) > best_score:
            best_payloads = payloads
            best_score = len(payloads)

    return best_payloads


def recover_file_bytes_from_samples(
    samples: Sequence[float],
    config: BaudcastConfig = DEFAULT_CONFIG,
) -> bytes:
    """Recover file bytes from audio samples."""
    best_bytes = b""
    best_score = -1
    max_offset = min(config.samples_per_symbol, len(samples))

    for offset in range(max_offset):
        candidate_bits = samples_to_bits(samples, config, offset=offset)
        payloads = extract_payloads_from_bits(candidate_bits, config)
        if len(payloads) > best_score:
            best_bytes = extract_file_bytes_from_bits(candidate_bits, config)
            best_score = len(payloads)

    return best_bytes
