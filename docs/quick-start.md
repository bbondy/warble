# Quick Start

## What You Need

- Python 3.11 or newer
- A virtual environment
- For live audio transfer: working speaker and microphone access through PortAudio and the `sounddevice` Python package

## Install

For normal use:

```bash
python -m pip install -e .
```

For development with tests:

```bash
python -m pip install -e '.[dev]'
```

## First Run Without Audio Hardware

Start with the in-memory demo:

```bash
python3 demo.py
```

Expected behavior:

- the program prints `Hello World`
- no microphone or speaker is used

This verifies the encoder and decoder logic without involving device permissions.

## Inspect Audio Devices

Before using live transfer, list PortAudio devices:

```bash
python3 -m baudcast devices
```

If the default device is wrong, pass `--device <id>` to `send` or `receive`.

## Send a File

```bash
python3 -m baudcast send ./message.txt
```

What happens:

1. `baudcast/cli.py` reads `message.txt`
2. `baudcast/modulator.py` converts it into audio samples
3. `baudcast/audio_io.py` plays those samples

## Receive a File

```bash
python3 -m baudcast receive -o ./received.txt
```

What happens:

1. `baudcast/audio_io.py` records microphone input
2. `baudcast/demodulator.py` converts samples into bits
3. `baudcast/framing.py` extracts payloads and checks CRC
4. `baudcast/cli.py` writes the result to `received.txt`

The default record time is `15` seconds. To change it:

```bash
python3 -m baudcast receive -o ./received.txt --seconds 5
```

## Matching Sender and Receiver Settings

The sender and receiver must use the same signal settings.

The important ones are:

- `--freq0`
- `--freq1`
- `--baud`
- `--sample-rate`

If these do not match, decode quality will drop sharply because the receiver will be looking for the wrong tones or the wrong symbol duration.

## Run Tests

```bash
python -m pytest
```

These tests do not require live audio devices because they exercise the protocol and signal logic in memory.
