"""Small utility helpers for binary conversion and chunking."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence


def bytes_to_bits(data: bytes) -> list[int]:
    """Convert bytes into a list of bits using MSB-first ordering."""
    bits: list[int] = []
    for value in data:
        for shift in range(7, -1, -1):
            bits.append((value >> shift) & 1)
    return bits


def bits_to_bytes(bits: Sequence[int]) -> bytes:
    """Convert a bit sequence into bytes using MSB-first ordering."""
    if len(bits) % 8 != 0:
        raise ValueError("bit sequence length must be a multiple of 8")

    output = bytearray()
    for offset in range(0, len(bits), 8):
        value = 0
        for bit in bits[offset : offset + 8]:
            value = (value << 1) | int(bit)
        output.append(value)
    return bytes(output)


def chunk_bytes(data: bytes, chunk_size: int) -> Iterator[bytes]:
    """Yield fixed-size byte chunks from data."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    for offset in range(0, len(data), chunk_size):
        yield data[offset : offset + chunk_size]


def flatten_bytes(chunks: Iterable[bytes]) -> bytes:
    """Join a stream of byte chunks into a single byte string."""
    return b"".join(chunks)
