"""Audio recording utilities for Beacon.

This module provides simple audio capture from the system's default microphone.
It returns a file handle suitable for uploading to transcription APIs.

Key Features:
- Records in WAV format for maximum compatibility
- 16kHz sample rate optimized for speech recognition
- Mono channel to reduce file size
- Automatic resource cleanup

Dependencies:
  - sounddevice: Cross-platform audio I/O
  - soundfile: Audio file encoding/decoding

Example:
    >>> from recorder import record_mic
    >>> audio_file = record_mic(5.0)  # Record 5 seconds
    >>> # Use audio_file with transcription API
    >>> audio_file.close()
"""

from __future__ import annotations


import os
import tempfile
from typing import BinaryIO

from playsound3 import playsound
import sounddevice as sd
import soundfile as sf

__all__ = ["record_mic"]


def record_mic(
    duration_seconds: float,
    *,
    samplerate: int = 16_000,
    channels: int = 1,
    subtype: str = "PCM_16",
    beep: bool = True,
) -> BinaryIO:
    """Record audio from the default microphone and return a file handle.

    This function captures audio for the specified duration and returns a
    file handle that can be passed directly to transcription APIs.

    Parameters:
        duration_seconds: Number of seconds to record (float or int).
        samplerate: Sample rate in Hz (default: 16000, optimal for speech).
        channels: Number of channels - 1 for mono, 2 for stereo (default: 1).
        subtype: WAV encoding format (default: "PCM_16" for 16-bit PCM).

    Returns:
        An open binary file object (mode 'rb') pointing to a temporary .wav file.
        The caller MUST close this file handle when done.

    Raises:
        ValueError: If parameters are invalid (negative duration, etc.).
        RuntimeError: If recording fails due to device or driver errors.

    Example:
        >>> audio_file = record_mic(3.0)
        >>> try:
        ...     # Use audio_file with your API
        ...     pass
        ... finally:
        ...     audio_file.close()
    """

    # Validate parameters
    if duration_seconds is None or duration_seconds <= 0:
        raise ValueError("duration_seconds must be a positive number")
    if samplerate <= 0:
        raise ValueError("samplerate must be positive")
    if channels not in (1, 2):
        raise ValueError("channels must be 1 (mono) or 2 (stereo)")
    if beep:
        playsound('beep1.wav')  # You must have a beep.wav file

    # Calculate total frames needed
    frames = int(round(duration_seconds * samplerate))
    
    # sounddevice uses float32 for capture; we'll convert to PCM_16 on write
    dtype = "float32"

    # Capture audio from microphone
    try:
        print(f"🎤 Recording {duration_seconds} seconds...")
        recording = sd.rec(
            frames=frames, 
            samplerate=samplerate, 
            channels=channels, 
            dtype=dtype
        )
        sd.wait()  # Block until recording is complete
        print("✓ Recording complete")
    except Exception as exc:
        raise RuntimeError(f"Microphone recording failed: {exc}") from exc

    # Create temporary file for the recording
    # Using NamedTemporaryFile ensures we get a real filename that can be
    # used reliably across different platforms and upload libraries
    tmp = tempfile.NamedTemporaryFile(
        prefix="beacon_recording_", 
        suffix=".wav", 
        delete=False
    )
    tmp_path = tmp.name
    tmp.close()  # Close so soundfile can open it reliably on all platforms

    # Write the recording to WAV format
    try:
        sf.write(tmp_path, recording, samplerate=samplerate, subtype=subtype)
    except Exception as exc:
        raise RuntimeError(f"Failed to encode/write WAV audio: {exc}") from exc

    # Reopen as binary for reading and return
    # The caller will use this handle with their API, then close it
    if beep:
        playsound('beep2.wav')
    return open(tmp_path, "rb")


if __name__ == "__main__":
    # Simple test: record 3 seconds and show file info
    print("Testing microphone recording...")
    f = record_mic(3)
    try:
        print(f"✓ Successfully recorded to: {getattr(f, 'name', '<memory>')}")
        print(f"✓ File size: {os.path.getsize(f.name) if hasattr(f, 'name') else 'unknown'} bytes")
    finally:
        f.close()
        print("✓ Test complete")