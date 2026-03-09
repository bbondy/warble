"""Configuration values for the Warble protocol."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WarbleConfig:
    """Static protocol and signal parameters."""

    sample_rate: int = 44_100
    freq0: float = 1_200.0
    freq1: float = 2_400.0
    baud: int = 100
    amplitude: float = 0.8
    max_payload_size: int = 255
    preamble: bytes = b"\xaa" * 4

    @property
    def symbol_duration(self) -> float:
        return 1.0 / self.baud

    @property
    def samples_per_symbol(self) -> int:
        return max(1, round(self.sample_rate / self.baud))


DEFAULT_CONFIG = WarbleConfig()
