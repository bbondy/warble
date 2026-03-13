# How Baudcast Works

This document follows the real code path through the repository.

The easiest mental model is:

- `framing.py` decides how bytes are packaged
- `modulator.py` turns those packaged bits into sound
- `demodulator.py` turns sound back into bits
- `audio_io.py` handles live speaker and microphone access

## Start With the Safe Demo

Run:

```bash
python3 demo.py
```

`demo.py` does not touch your audio hardware. It keeps everything in memory:

1. `file_bytes_to_samples(message, DEFAULT_CONFIG)` in `baudcast/modulator.py`
2. `recover_file_bytes_from_samples(samples, DEFAULT_CONFIG)` in `baudcast/demodulator.py`

If you are new to the codebase, this is the cleanest place to start because it exercises the core encoder and decoder without involving PortAudio, device IDs, or microphone permissions.

## Step 1: Configuration

The shared settings live in `baudcast/config.py`.

`BaudcastConfig` defines:

- `sample_rate = 44100`: how many audio samples are used per second
- `freq0 = 1200.0`: the tone for bit `0`
- `freq1 = 2400.0`: the tone for bit `1`
- `baud = 100`: how many symbols are transmitted per second
- `amplitude = 0.8`: playback volume scaling
- `max_payload_size = 255`: maximum bytes per frame payload
- `preamble = b"\\xaa" * 4`: frame start marker

Two computed properties matter a lot:

- `symbol_duration`: `1 / baud`
- `samples_per_symbol`: `round(sample_rate / baud)`

A "symbol" here means one fixed slice of audio that carries one bit.

## Step 2: Sending a File

The send command starts in `baudcast/cli.py` inside `_handle_send()`.

### 2.1 Read file bytes

```python
data = args.path.read_bytes()
```

At this point the program just has the raw file contents in memory.

### 2.2 Split bytes into frames

`_handle_send()` calls:

```python
samples = file_bytes_to_samples(data, config)
```

That leads into `baudcast/modulator.py:file_bytes_to_samples()`, which immediately calls:

```python
build_file_frames(data, config)
```

inside `baudcast/framing.py`.

`build_file_frames()` does two important things:

1. Splits the file into chunks of at most `255` bytes using `chunk_file_bytes()`
2. Appends one extra empty frame by calling `encode_frame(b"", config)`

That empty frame is the end-of-file marker. The receiver uses it to know when to stop joining payloads.

### 2.3 Build one frame

`encode_frame()` builds:

```text
[preamble][length][payload][crc]
```

For example, a short payload becomes:

- `preamble`: `0xaa 0xaa 0xaa 0xaa`
- `length`: one byte
- `payload`: the actual file chunk
- `crc`: two bytes from `crc16_ccitt(payload)`

This framing exists so the receiver can answer two questions:

1. "Where does a frame start?"
2. "Did I decode the payload correctly?"

## Step 3: Turning Frames Into Audio

Still inside `baudcast/modulator.py`:

### 3.1 Convert frame bytes to bits

`frames_to_samples()` loops over frames and uses:

```python
frame_to_bits(frame)
```

`frame_to_bits()` is just a thin wrapper around `bytes_to_bits()` from `baudcast/utils.py`.

The bit order is most-significant-bit first. That means the code sends the leftmost bit of each byte first.

### 3.2 Convert bits to tones

`bits_to_samples()` precomputes two one-symbol waveforms:

- `zero_symbol = generate_tone(config.freq0, ...)`
- `one_symbol = generate_tone(config.freq1, ...)`

Then it appends one of those symbol waveforms for every bit.

So if the bitstream is:

```text
0 1 1 0
```

the output audio is:

```text
1200 Hz tone, 2400 Hz tone, 2400 Hz tone, 1200 Hz tone
```

with each tone lasting exactly one symbol.

### 3.3 Play the samples

Back in `_handle_send()` the code calls:

```python
play_samples(samples, config.sample_rate, device=args.device)
```

in `baudcast/audio_io.py`.

That function:

1. Imports `sounddevice`
2. Validates the chosen output device
3. Calls `sounddevice.play(..., blocking=True)`

"Blocking" means the function waits until playback is finished before returning.

## Step 4: Receiving a File

The receive command starts in `baudcast/cli.py` inside `_handle_receive()`.

### 4.1 Record audio

The first side effect is:

```python
samples = record_samples(args.seconds, config.sample_rate, device=args.device)
```

`record_samples()` in `baudcast/audio_io.py` records mono `float32` samples and returns them as a Python `list[float]`.

### 4.2 Recover payloads from the recording

The next call is:

```python
payloads = recover_payloads_from_samples(samples, config)
```

in `baudcast/demodulator.py`.

This function is one of the most important pieces of the repository.

Why? Because the receiver usually does not know the exact sample index where a symbol starts.

If you cut the recording into windows at the wrong offset, bit detection gets worse. So the code tries many offsets:

```python
for offset in range(max_offset):
    candidate_bits = samples_to_bits(samples, config, offset=offset)
    payloads = extract_payloads_from_bits(candidate_bits, config)
```

It keeps the offset that produces the most valid frames.

This is a simple but practical strategy for unknown symbol alignment.

### 4.3 Detect one bit from one symbol window

Inside `samples_to_bits()`, the recording is sliced into chunks of `config.samples_per_symbol`.

Each chunk goes to:

```python
detect_bit(symbol_samples, config)
```

`detect_bit()` compares two measurements:

- energy near `freq0`
- energy near `freq1`

Those measurements come from `goertzel_magnitude()`.

If the `freq1` energy is greater or equal, the bit is `1`. Otherwise it is `0`.

This means the decoder does not try to reconstruct a full waveform. It asks a narrower question: "Which of my two expected tones is stronger in this time window?"

## Step 5: Turning Bits Back Into File Bytes

After `samples_to_bits()` produces a bitstream, the demodulator passes it into:

```python
extract_payloads_from_bits(candidate_bits, config)
```

in `baudcast/framing.py`.

### 5.1 Search for the preamble

`extract_payloads_from_bits()` scans through the bitstream until it finds the preamble bits.

This is how it finds likely frame boundaries.

### 5.2 Read the length byte

Once the preamble matches, the function reads the next 8 bits as the payload length.

That tells it how many more payload bits and CRC bits to expect.

### 5.3 Validate the frame

The candidate frame bits are converted back into bytes with `bits_to_bytes()`, then passed to:

```python
decode_frame(...)
```

`decode_frame()` checks:

1. minimum frame size
2. preamble presence
3. length consistency
4. CRC correctness

If CRC validation fails, the frame is rejected and the scanner continues.

### 5.4 Reassemble the file

Back in `baudcast/cli.py`, `_handle_receive()` calls:

```python
data = recover_file_bytes(payloads)
```

`recover_file_bytes()` appends payloads until it reaches the empty payload `b""`.

That empty payload is the explicit end-of-file marker added on the send side.

Finally the CLI writes the reconstructed bytes to disk with:

```python
args.output.write_bytes(data)
```

## What the Tests Prove

The tests are small, but they describe the repository well.

### `tests/test_framing.py`

This file explains the frame format and error handling:

- CRC matches a known reference value
- encoded frames decode back to the original payload
- corrupted frames raise `CRCMismatchError`
- multiple frames can be found inside noisy surrounding bits
- end-of-file handling stops reconstruction at the empty frame

### `tests/test_modulator.py`

This file shows that:

- one generated tone has the expected symbol length
- concatenating bits produces the expected total sample length
- a tone really has stronger energy at its target frequency

### `tests/test_demodulator.py`

This file is especially helpful for beginners because it shows the receive side tolerating timing shifts.

Two tests prepend dummy samples before the real signal:

- `test_recover_payloads_from_shifted_samples()`
- `test_recover_file_bytes_from_samples_round_trip()`

Those tests explain why the demodulator tries multiple offsets.

## Where Side Effects Happen

Most files are pure logic. That makes the repository easier to test.

The main side-effect locations are:

- `Path.read_bytes()` in `baudcast/cli.py`
- `Path.write_bytes()` in `baudcast/cli.py`
- `sounddevice.play()` in `baudcast/audio_io.py`
- `sounddevice.rec()` in `baudcast/audio_io.py`
- `print()` calls in `baudcast/cli.py` and `demo.py`

If you want to change protocol logic safely, stay mostly inside `framing.py`, `modulator.py`, and `demodulator.py`.

If you want to change hardware behavior, inspect `audio_io.py`.
