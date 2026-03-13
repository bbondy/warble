# Debugging Guide

## Start With the Simplest Check

Run:

```bash
python3 demo.py
```

If this fails, the problem is in the pure Python encoder or decoder logic, not in your microphone or speaker setup.

## If `send` or `receive` Cannot Use Audio Devices

First inspect the available devices:

```bash
python3 -m baudcast devices
```

Then retry with an explicit device ID:

```bash
python3 -m baudcast send ./message.txt --device 3
python3 -m baudcast receive -o ./received.txt --device 1
```

Relevant code:

- device enumeration: `baudcast/audio_io.py:list_devices()`
- device validation: `baudcast/audio_io.py:_validate_device()`

Common causes:

- macOS microphone permissions are missing
- the default device is not the device you expected
- the selected device does not support the requested sample rate

## If `receive` Prints `No valid frames detected.`

This message is raised in `baudcast/cli.py:_handle_receive()` when `recover_payloads_from_samples()` returns an empty list.

That usually means one of these things happened:

1. The recording did not contain a strong enough Baudcast signal.
2. Sender and receiver used different protocol settings.
3. The recording window missed part of the transmission.
4. The speaker and microphone introduced too much noise or distortion.

Checks to perform:

- make sure `--freq0`, `--freq1`, `--baud`, and `--sample-rate` match on both sides
- increase `--seconds` on the receiver
- move the speaker and microphone closer together
- reduce background noise

Relevant code path:

`baudcast/cli.py`
-> `record_samples()`
-> `recover_payloads_from_samples()`
-> `samples_to_bits()`
-> `extract_payloads_from_bits()`

## If You Suspect Frame Corruption

Inspect `baudcast/framing.py`.

The receiver rejects frames when `decode_frame()` raises:

- `FrameError`
- `CRCMismatchError`

The CRC logic is implemented in `crc16_ccitt()`.

The best quick check is:

```bash
python -m pytest tests/test_framing.py
```

## If You Suspect Tone Detection Problems

Inspect:

- `baudcast/modulator.py:generate_tone()`
- `baudcast/demodulator.py:goertzel_magnitude()`
- `baudcast/demodulator.py:detect_bit()`

The most targeted tests are:

```bash
python -m pytest tests/test_modulator.py tests/test_demodulator.py
```

These confirm that:

- generated tones have the expected target-frequency energy
- bit detection works for the two configured frequencies
- decoding tolerates leading sample offsets

## Safe Places To Modify Code

### Change the frame format

Edit `baudcast/framing.py` and then run:

```bash
python -m pytest tests/test_framing.py tests/test_demodulator.py
```

Be careful: sender and receiver must agree on the same format.

### Change signal parameters

Edit defaults in `baudcast/config.py` or pass CLI flags in `baudcast/cli.py`.

Be careful: changing `baud`, `freq0`, `freq1`, or `sample_rate` affects both encoding and decoding.

### Change live audio behavior

Edit `baudcast/audio_io.py`.

This is the right place for device selection and recording/playback behavior. Avoid mixing hardware code into `framing.py` or `demodulator.py`.
