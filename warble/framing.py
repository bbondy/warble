"""Frame packing and unpacking for Warble transmissions."""

from __future__ import annotations

from collections.abc import Sequence

from warble.config import DEFAULT_CONFIG, WarbleConfig
from warble.utils import bits_to_bytes, bytes_to_bits, chunk_bytes


class FrameError(ValueError):
    """Base exception for invalid frames."""


class CRCMismatchError(FrameError):
    """Raised when a frame CRC does not match its payload."""


def crc16_ccitt(data: bytes, *, initial: int = 0xFFFF, polynomial: int = 0x1021) -> int:
    """Compute a CRC-16/CCITT-FALSE checksum."""
    crc = initial
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ polynomial) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def encode_frame(payload: bytes, config: WarbleConfig = DEFAULT_CONFIG) -> bytes:
    """Build a framed payload with preamble, length, and CRC."""
    if len(payload) > config.max_payload_size:
        raise ValueError(f"payload exceeds max frame size of {config.max_payload_size} bytes")

    header = config.preamble + bytes([len(payload)])
    checksum = crc16_ccitt(payload).to_bytes(2, "big")
    return header + payload + checksum


def decode_frame(frame: bytes, config: WarbleConfig = DEFAULT_CONFIG) -> bytes:
    """Validate and unpack a single frame."""
    min_size = len(config.preamble) + 1 + 2
    if len(frame) < min_size:
        raise FrameError("frame is too short")
    if not frame.startswith(config.preamble):
        raise FrameError("missing preamble")

    payload_length = frame[len(config.preamble)]
    expected_size = len(config.preamble) + 1 + payload_length + 2
    if len(frame) != expected_size:
        raise FrameError("frame length does not match payload length")

    payload_start = len(config.preamble) + 1
    payload_end = payload_start + payload_length
    payload = frame[payload_start:payload_end]
    expected_crc = int.from_bytes(frame[payload_end:payload_end + 2], "big")
    actual_crc = crc16_ccitt(payload)
    if actual_crc != expected_crc:
        raise CRCMismatchError("crc mismatch")
    return payload


def frame_to_bits(frame: bytes) -> list[int]:
    """Convert a frame into its transmitted bit order."""
    return bytes_to_bits(frame)


def extract_payloads_from_bits(
    bits: Sequence[int],
    config: WarbleConfig = DEFAULT_CONFIG,
) -> list[bytes]:
    """Recover all valid frame payloads from a bitstream."""
    preamble_bits = bytes_to_bits(config.preamble)
    preamble_length = len(preamble_bits)
    minimum_bits = preamble_length + 8 + 16
    recovered: list[bytes] = []
    index = 0

    while index <= len(bits) - minimum_bits:
        if list(bits[index:index + preamble_length]) != preamble_bits:
            index += 1
            continue

        length_bits = bits[index + preamble_length:index + preamble_length + 8]
        payload_length = bits_to_bytes(length_bits)[0]
        frame_bit_length = preamble_length + 8 + (payload_length * 8) + 16
        frame_end = index + frame_bit_length
        if frame_end > len(bits):
            break

        frame_bits = bits[index:frame_end]
        try:
            payload = decode_frame(bits_to_bytes(frame_bits), config)
        except FrameError:
            index += 1
            continue

        recovered.append(payload)
        index = frame_end

    return recovered


def chunk_file_bytes(data: bytes, config: WarbleConfig = DEFAULT_CONFIG) -> list[bytes]:
    """Split a file into frame-sized payloads."""
    return list(chunk_bytes(data, config.max_payload_size))
