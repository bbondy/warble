# Glossary

## Concept: FSK

### Plain explanation

FSK means the program sends different bit values using different tone frequencies.

In Baudcast, bit `0` uses `1200 Hz` and bit `1` uses `2400 Hz`.

### Analogy

Imagine two whistles. One whistle means "zero" and the other means "one".

### Short definition

Frequency-shift keying is a modulation method where symbols are represented by different frequencies.

### Where it appears in this repository

Configured in `baudcast/config.py` through `freq0` and `freq1`, generated in `baudcast/modulator.py`, and detected in `baudcast/demodulator.py`.

## Concept: Symbol

### Plain explanation

A symbol is one fixed-size chunk of signal time.

In this repository, each symbol carries exactly one bit.

### Analogy

Think of a song made of equal-sized beats. Each beat must contain exactly one note choice.

### Short definition

A symbol is one unit of transmitted signal that represents one or more bits.

### Where it appears in this repository

`BaudcastConfig.samples_per_symbol` in `baudcast/config.py` decides how many audio samples belong to one symbol. `generate_tone()` in `baudcast/modulator.py` creates one symbol worth of samples.

## Concept: Sample Rate

### Plain explanation

Sample rate tells you how many numeric audio measurements are stored each second.

Higher sample rates give the code more points to describe a waveform.

### Analogy

It is like how many dots per second you use to draw a moving line.

### Short definition

The number of audio samples captured or played per second.

### Where it appears in this repository

Defined by `BaudcastConfig.sample_rate` in `baudcast/config.py` and passed into `sounddevice.play()` and `sounddevice.rec()` in `baudcast/audio_io.py`.

## Concept: Frame

### Plain explanation

A frame is a small package of bytes with extra metadata around it.

The extra metadata helps the receiver figure out where the package starts, how long it is, and whether it was damaged.

### Analogy

It is like putting a letter into an envelope that also includes the address and a tamper check.

### Short definition

A frame is a structured protocol unit containing payload data plus control information.

### Where it appears in this repository

Built by `encode_frame()` and validated by `decode_frame()` in `baudcast/framing.py`.

## Concept: Preamble

### Plain explanation

A preamble is a recognizable start pattern placed before each frame.

It gives the receiver something specific to search for in a long bitstream.

### Analogy

It is like shouting "start of message" before speaking the actual message.

### Short definition

A fixed marker sequence used to identify the start of a transmitted frame.

### Where it appears in this repository

Configured as `b"\\xaa" * 4` in `baudcast/config.py` and scanned for in `extract_payloads_from_bits()` in `baudcast/framing.py`.

## Concept: CRC

### Plain explanation

CRC is a quick error check. The sender computes a short value from the payload, and the receiver computes it again to see whether the payload changed.

It does not repair errors. It only helps detect them.

### Analogy

It is like writing a small checksum number on a package so the receiver can tell if the contents were altered in transit.

### Short definition

A cyclic redundancy check is an error-detection code computed from transmitted data.

### Where it appears in this repository

Implemented by `crc16_ccitt()` in `baudcast/framing.py` and checked inside `decode_frame()`.

## Concept: Bitstream

### Plain explanation

A bitstream is just a long sequence of `0` and `1` values.

Baudcast turns frames into a bitstream before making audio, and rebuilds a bitstream from audio before decoding frames.

### Analogy

It is like a long ribbon of black and white squares that later gets grouped back into meaningful packages.

### Short definition

A bitstream is an ordered sequence of bits transmitted or processed as a continuous stream.

### Where it appears in this repository

Created from frame bytes by `frame_to_bits()` in `baudcast/framing.py` and reconstructed from audio by `samples_to_bits()` in `baudcast/demodulator.py`.

## Concept: Goertzel Algorithm

### Plain explanation

The Goertzel algorithm checks how strong one chosen frequency is inside a block of samples.

Baudcast uses it because the decoder only cares about two frequencies: the one for `0` and the one for `1`.

### Analogy

Imagine listening to a chord and asking, "How loud is middle C specifically?" instead of analyzing every possible note.

### Short definition

A signal-processing algorithm for efficiently measuring the energy of specific target frequencies in sampled data.

### Where it appears in this repository

Implemented in `goertzel_magnitude()` in `baudcast/demodulator.py` and used by `detect_bit()`.

## Concept: Offset Search

### Plain explanation

Offset search means trying different starting positions when slicing the recording into symbol-sized windows.

This matters because the receiver does not know the exact sample where the sender started a symbol.

### Analogy

It is like cutting a loaf of bread into equal slices after someone already started cutting, so you try several starting points to line up with the existing cuts.

### Short definition

A decoding strategy that tests multiple candidate alignments to find the most plausible symbol boundaries.

### Where it appears in this repository

Implemented in `recover_payloads_from_samples()` and `recover_file_bytes_from_samples()` in `baudcast/demodulator.py`.
