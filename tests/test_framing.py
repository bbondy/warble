"""Tests for Baudcast framing primitives."""

from __future__ import annotations

import unittest

from baudcast.framing import CRCMismatchError, build_file_frames, chunk_file_bytes, crc16_ccitt, decode_frame, encode_frame, extract_file_bytes_from_bits, extract_payloads_from_bits, frame_to_bits, recover_file_bytes


class FramingTests(unittest.TestCase):
    def test_crc16_matches_known_vector(self) -> None:
        self.assertEqual(crc16_ccitt(b"123456789"), 0x29B1)

    def test_encode_decode_round_trip(self) -> None:
        payload = b"hello world"
        frame = encode_frame(payload)
        self.assertEqual(decode_frame(frame), payload)

    def test_decode_rejects_corrupt_frame(self) -> None:
        frame = bytearray(encode_frame(b"payload"))
        frame[-1] ^= 0x01
        with self.assertRaises(CRCMismatchError):
            decode_frame(bytes(frame))

    def test_extract_payloads_from_bitstream_recovers_multiple_frames(self) -> None:
        stream_bits = [0, 0, 1, 1]
        stream_bits.extend(frame_to_bits(encode_frame(b"alpha")))
        stream_bits.extend([1, 0, 1])
        stream_bits.extend(frame_to_bits(encode_frame(b"beta")))

        self.assertEqual(extract_payloads_from_bits(stream_bits), [b"alpha", b"beta"])

    def test_chunk_file_bytes_uses_frame_payload_limit(self) -> None:
        data = bytes(range(256)) * 2
        chunks = chunk_file_bytes(data)
        self.assertEqual(len(chunks[0]), 255)
        self.assertEqual(sum(len(chunk) for chunk in chunks), len(data))

    def test_build_file_frames_ends_with_eof_frame(self) -> None:
        frames = build_file_frames(b"abc")
        self.assertEqual(decode_frame(frames[-1]), b"")

    def test_recover_file_bytes_stops_at_eof(self) -> None:
        self.assertEqual(recover_file_bytes([b"abc", b"def", b"", b"ignored"]), b"abcdef")

    def test_extract_file_bytes_from_bits_round_trip(self) -> None:
        bits: list[int] = []
        for frame in build_file_frames(b"hello there"):
            bits.extend(frame_to_bits(frame))
        self.assertEqual(extract_file_bytes_from_bits(bits), b"hello there")


if __name__ == "__main__":
    unittest.main()
