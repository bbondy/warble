"""Tests for Baudcast sample decoding."""

from __future__ import annotations

import unittest

from baudcast.demodulator import detect_bit, recover_file_bytes_from_samples, recover_payloads_from_samples, samples_to_bits
from baudcast.framing import build_file_frames, encode_frame, frame_to_bits
from baudcast.modulator import bits_to_samples, generate_tone


class DemodulatorTests(unittest.TestCase):
    def test_detect_bit_recognizes_zero_symbol(self) -> None:
        self.assertEqual(detect_bit(generate_tone(1_200.0)), 0)

    def test_detect_bit_recognizes_one_symbol(self) -> None:
        self.assertEqual(detect_bit(generate_tone(2_400.0)), 1)

    def test_samples_to_bits_round_trip(self) -> None:
        bits = [0, 1, 0, 1, 1, 0, 0, 1]
        samples = bits_to_samples(bits)
        self.assertEqual(samples_to_bits(samples), bits)

    def test_recover_payloads_from_shifted_samples(self) -> None:
        payloads = [b"first", b"second"]
        bits = []
        for payload in payloads:
            bits.extend(frame_to_bits(encode_frame(payload)))
        shifted_samples = ([0.0] * 17) + bits_to_samples(bits)
        self.assertEqual(recover_payloads_from_samples(shifted_samples), payloads)

    def test_recover_file_bytes_from_samples_round_trip(self) -> None:
        bits = []
        for frame in build_file_frames(b"loopback bytes"):
            bits.extend(frame_to_bits(frame))
        shifted_samples = ([0.0] * 11) + bits_to_samples(bits)
        self.assertEqual(recover_file_bytes_from_samples(shifted_samples), b"loopback bytes")


if __name__ == "__main__":
    unittest.main()
