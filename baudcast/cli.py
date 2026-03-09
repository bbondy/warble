"""Command-line interface for Baudcast."""

from __future__ import annotations

import argparse
from pathlib import Path

from baudcast.audio_io import list_devices, play_samples, record_samples
from baudcast.config import BaudcastConfig
from baudcast.demodulator import recover_payloads_from_samples
from baudcast.framing import recover_file_bytes
from baudcast.modulator import file_bytes_to_samples


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="baudcast", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    devices_parser = subparsers.add_parser("devices", help="list audio devices")
    devices_parser.set_defaults(handler=_handle_devices)

    send_parser = subparsers.add_parser("send", help="encode and play a file")
    send_parser.add_argument("path", type=Path, help="file to transmit")
    _add_common_signal_args(send_parser)
    send_parser.add_argument("--device", type=int, help="output device index")
    send_parser.set_defaults(handler=_handle_send)

    receive_parser = subparsers.add_parser("receive", help="record audio and decode a file")
    receive_parser.add_argument("-o", "--output", type=Path, required=True, help="output file path")
    receive_parser.add_argument("--seconds", type=float, default=15.0, help="recording duration")
    _add_common_signal_args(receive_parser)
    receive_parser.add_argument("--device", type=int, help="input device index")
    receive_parser.set_defaults(handler=_handle_receive)

    return parser


def _add_common_signal_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--freq0", type=float, default=1_200.0, help="frequency for bit 0")
    parser.add_argument("--freq1", type=float, default=2_400.0, help="frequency for bit 1")
    parser.add_argument("--baud", type=int, default=100, help="symbols per second")
    parser.add_argument("--sample-rate", type=int, default=44_100, help="audio sample rate")
    parser.add_argument("--volume", type=float, default=0.8, help="output amplitude")


def _config_from_args(args: argparse.Namespace) -> BaudcastConfig:
    return BaudcastConfig(
        sample_rate=args.sample_rate,
        freq0=args.freq0,
        freq1=args.freq1,
        baud=args.baud,
        amplitude=args.volume,
    )


def _handle_devices(_: argparse.Namespace) -> int:
    for description in list_devices():
        print(description)
    return 0


def _handle_send(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    data = args.path.read_bytes()
    samples = file_bytes_to_samples(data, config)
    print(f"Sending {len(data)} bytes as {len(samples)} audio samples")
    play_samples(samples, config.sample_rate, device=args.device)
    return 0


def _handle_receive(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    print(f"Recording {args.seconds:.1f}s of audio...")
    samples = record_samples(args.seconds, config.sample_rate, device=args.device)
    payloads = recover_payloads_from_samples(samples, config)
    if not payloads:
        raise SystemExit("No valid frames detected.")

    data = recover_file_bytes(payloads)
    args.output.write_bytes(data)
    print(f"Wrote {len(data)} bytes to {args.output}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the Baudcast CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)
