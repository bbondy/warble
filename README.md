# Baudcast

Transfer files between computers using sound waves (speaker to microphone).

Baudcast is a Python CLI tool that encodes files as audio tones and decodes them back. It works like an old-school modem, but through the air instead of phone lines.

If you are new to the repository, start with these docs in order:

1. [docs/repo-map.md](docs/repo-map.md)
2. [docs/how-it-works.md](docs/how-it-works.md)
3. [docs/quick-start.md](docs/quick-start.md)
4. [docs/debugging.md](docs/debugging.md)
5. [docs/glossary.md](docs/glossary.md)

## How It Works

Baudcast uses 2-FSK modulation. Each bit is represented by one of two audio tones:

| Bit | Tone |
| --- | --- |
| 0 | 1200 Hz |
| 1 | 2400 Hz |

Each tone lasts 10 ms, yielding 100 symbols per second.

To transfer data reliably, bytes are wrapped in a simple frame:

```text
+----------+--------+---------+-----+
| Preamble | Length | Payload | CRC |
+----------+--------+---------+-----+
| 4 bytes  | 1 byte | N bytes | 2 b |
+----------+--------+---------+-----+
```

- Preamble: `10101010` repeated 4 times
- Length: payload size in bytes
- Payload: frame data
- CRC-16: frame integrity check

On send, Baudcast reads file bytes, packs them into frames, converts frame bits into tones, and plays the resulting waveform through a speaker.

On receive, Baudcast records audio from a microphone, slices it into symbol windows, measures which target frequency is stronger for each symbol, reconstructs the bitstream, finds frame boundaries from the preamble, and verifies integrity with CRC before writing the recovered bytes back to disk.

## Quick Start

```bash
python3 demo.py
```

The safest first run is `demo.py`. It exercises the encoder and decoder entirely in memory, so it does not require live audio devices.

Install the project into your virtualenv:

```bash
python -m pip install -e .
```

For local development with tests:

```bash
python -m pip install -e '.[dev]'
```

Then run either side of the transfer:

```bash
python3 -m baudcast devices
python3 -m baudcast send ./message.txt
python3 -m baudcast receive -o ./message.txt
```

For a fuller beginner setup guide, see [docs/quick-start.md](docs/quick-start.md).

## Repository Tour

- [docs/repo-map.md](docs/repo-map.md): project purpose, entrypoints, major files, and execution overview
- [docs/how-it-works.md](docs/how-it-works.md): send and receive flow traced through the real code
- [docs/debugging.md](docs/debugging.md): where to look when audio I/O, framing, or decoding fail
- [docs/glossary.md](docs/glossary.md): beginner explanations of the signal-processing terms used in the code

## License

MIT
