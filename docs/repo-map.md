# Repository Map

## Project Purpose

Baudcast sends a file from one computer to another by turning the file into audible tones and then decoding those tones back into bytes.

In code terms, the project does four things:

1. Reads file bytes from disk.
2. Wraps those bytes into small frames with a checksum.
3. Converts frame bits into audio samples for playback.
4. Records audio, detects the transmitted bits, validates the frames, and writes the recovered file.

If you only read a few files first, read these in order:

1. `README.md`
2. `baudcast/cli.py`
3. `baudcast/framing.py`
4. `baudcast/modulator.py`
5. `baudcast/demodulator.py`
6. `baudcast/audio_io.py`

## Entrypoints

### `python -m baudcast`

Execution starts in `baudcast/__main__.py`, which immediately calls `baudcast.cli.main()`.

That means the real command-line entrypoint is `baudcast/cli.py`.

### `baudcast`

`pyproject.toml` defines the console script:

```toml
[project.scripts]
baudcast = "baudcast.cli:main"
```

So running `baudcast send ...` and running `python -m baudcast send ...` reach the same `main()` function.

### `python3 demo.py`

`demo.py` is the safest starting point for a beginner because it does not need speakers or microphones.

It:

1. Creates the audio samples for `b"Hello World"`.
2. Immediately decodes those samples in memory.
3. Prints the decoded result.

This is the shortest path through the core protocol.

## Major Directories

### `baudcast/`

This is the application package.

- `cli.py`: command parsing and top-level workflow for `devices`, `send`, and `receive`
- `config.py`: protocol and signal settings such as baud rate, frequencies, and preamble
- `framing.py`: packs raw bytes into frames and verifies them on decode
- `modulator.py`: turns bits into waveform samples
- `demodulator.py`: turns waveform samples back into bits and payload bytes
- `audio_io.py`: thin wrapper around the `sounddevice` library
- `utils.py`: bit and byte conversion helpers

### `tests/`

Unit tests for the framing, signal generation, and decoding logic.

These tests are especially useful because they show the project working without live audio hardware.

## Major Modules

### `baudcast/cli.py`

This file answers the beginner question, "What commands does this project actually support?"

The three subcommands are:

- `devices`: list audio input/output devices
- `send <path>`: read a file, convert it to audio, and play it
- `receive -o <path>`: record audio, decode it, and write the output file

The handlers are small on purpose:

- `_handle_send()` reads file bytes and calls `file_bytes_to_samples()`
- `_handle_receive()` records audio, calls `recover_payloads_from_samples()`, then joins payloads with `recover_file_bytes()`

### `baudcast/framing.py`

This is the protocol layer.

Before bytes become sound, they are wrapped into frames with:

- a preamble, which is a recognizable start marker
- a one-byte payload length
- the payload itself
- a CRC checksum for corruption detection

Important functions:

- `encode_frame()`: builds one frame
- `decode_frame()`: validates one frame
- `build_file_frames()`: splits a full file into multiple frames and adds an empty frame as an end-of-file marker
- `extract_payloads_from_bits()`: searches a decoded bitstream for valid frames

### `baudcast/modulator.py`

This is the encoding side.

It takes bits and generates a list of float audio samples:

- `generate_tone()`: one symbol worth of sine-wave samples for one frequency
- `bits_to_samples()`: repeats either the `0` tone or `1` tone for each bit
- `file_bytes_to_samples()`: full send path from file bytes to playable audio

### `baudcast/demodulator.py`

This is the decoding side.

It does the reverse of the modulator:

- slices the recording into one-symbol windows
- measures which target frequency is stronger in each window
- reconstructs the bitstream
- searches for valid frames

Important functions:

- `goertzel_magnitude()`: measures energy at a specific frequency
- `detect_bit()`: decides whether a symbol window represents `0` or `1`
- `samples_to_bits()`: converts a recording into a bitstream
- `recover_payloads_from_samples()`: tries multiple sample offsets to compensate for unknown symbol alignment

### `baudcast/audio_io.py`

This file is deliberately small. Its job is not protocol logic. Its job is talking to PortAudio through the `sounddevice` package.

Important functions:

- `list_devices()`
- `play_samples()`
- `record_samples()`

If live audio fails, this file is one of the first places to inspect.

## Execution Flow Overview

### Send flow

`baudcast/cli.py:_handle_send()`
-> read file bytes from disk
-> `baudcast.modulator.file_bytes_to_samples()`
-> `baudcast.framing.build_file_frames()`
-> `baudcast.framing.frame_to_bits()`
-> `baudcast.modulator.bits_to_samples()`
-> `baudcast.audio_io.play_samples()`

### Receive flow

`baudcast/cli.py:_handle_receive()`
-> `baudcast.audio_io.record_samples()`
-> `baudcast.demodulator.recover_payloads_from_samples()`
-> `baudcast.demodulator.samples_to_bits()`
-> `baudcast.framing.extract_payloads_from_bits()`
-> `baudcast.framing.decode_frame()`
-> `baudcast.framing.recover_file_bytes()`
-> write bytes to disk

## Key Concepts

The project relies on a few signal-processing terms that are easy to miss when reading code:

- FSK: one bit value uses one tone, the other bit value uses another tone
- symbol: one fixed-duration tone window that carries one bit in this project
- preamble: a recognizable bit pattern that helps the receiver find frame boundaries
- CRC: a small checksum used to reject damaged frames
- Goertzel algorithm: a focused way to measure how much of one target frequency is present

See `docs/glossary.md` for beginner explanations of each term.

## Important Files To Read First

### For the shortest possible guided tour

1. `demo.py`
2. `baudcast/modulator.py`
3. `baudcast/demodulator.py`

### To understand the real CLI workflow

1. `baudcast/__main__.py`
2. `baudcast/cli.py`
3. `baudcast/audio_io.py`

### To understand the protocol format

1. `baudcast/config.py`
2. `baudcast/framing.py`
3. `tests/test_framing.py`

### To understand how decoding copes with timing offsets

1. `baudcast/demodulator.py`
2. `tests/test_demodulator.py`
