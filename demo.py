"""In-memory loopback demo for Baudcast."""

from __future__ import annotations

from baudcast.config import DEFAULT_CONFIG
from baudcast.demodulator import recover_file_bytes_from_samples
from baudcast.modulator import file_bytes_to_samples


def main() -> int:
    message = b"Hello World"
    samples = file_bytes_to_samples(message, DEFAULT_CONFIG)
    decoded = recover_file_bytes_from_samples(samples, DEFAULT_CONFIG)
    print(decoded.decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
