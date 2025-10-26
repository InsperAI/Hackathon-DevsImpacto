"""Audio handling for Beacon - recording, transcription, and text-to-speech."""
from openai import OpenAI
from typing import BinaryIO
import os
import tempfile
from threading import Event, Lock, Thread

import sounddevice as sd
import soundfile as sf

from recorder import record_mic
import librosa  # pip install librosa

class AudioHandler:
    """Handles audio recording, transcription, and text-to-speech for Beacon."""

    def __init__(self, openai_api_key: str | None = None, voice: str = "coral"):
        """Initialize the audio handler.
        
        Args:
            openai_api_key: OpenAI API key for transcription and TTS
            voice: Default voice for TTS (coral, alloy, echo, fable, onyx, nova, shimmer)
        """
        self.client = OpenAI(api_key=openai_api_key)
        self.default_voice = voice
        self._playback_lock = Lock()
        self._is_playing = Event()
        self._playback_thread: Thread | None = None

    def transcribe_audio(self, audio: BinaryIO) -> str:
        """Transcribe audio file to text using OpenAI Whisper.
        
        Args:
            audio: Binary file handle containing audio data
            
        Returns:
            Transcribed text string
        """
        try:
            transcription = self.client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=audio,
            )
            return transcription.text
        except Exception as exc:
            print(f"Transcription error: {exc}")
            raise

    def record_and_transcribe(self, duration_seconds: float = 5.0) -> str:
        """Capture audio via microphone and transcribe it.
        
        Args:
            duration_seconds: How long to record (default 5 seconds)
            
        Returns:
            Transcribed text string
        """
        audio_handle = None
        tmp_path = None
        
        try:
            audio_handle = record_mic(duration_seconds)
            tmp_path = getattr(audio_handle, "name", None)
            transcription = self.transcribe_audio(audio_handle)
            return transcription.strip()
        except Exception as exc:
            print(f"Recording or transcription failed: {exc}")
            raise
        finally:
            # Clean up resources
            if audio_handle:
                audio_handle.close()
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    def generate_speech(self, text: str, output_path: str, voice: str | None = None) -> None:
        """Generate speech audio file from text.
        
        Args:
            text: Text to convert to speech
            output_path: Where to save the audio file
            voice: Voice to use (or default if None)
        """
        if not text or text.strip() == "":
            print("Warning: Empty text provided for speech generation")
            return
            
        voice = voice or self.default_voice
        
        try:
            with self.client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",
                voice=voice,
                input=text,
                instructions="Speak in a clear, friendly, and helpful tone suitable for a blind user. Be concise but warm.",
            ) as response:
                response.stream_to_file(output_path)
        except Exception as exc:
            print(f"Speech generation error: {exc}")
            raise

    def stop_playback(self) -> None:
        """Stop any active audio playback immediately."""
        with self._playback_lock:
            active_thread = self._playback_thread
        if active_thread and active_thread.is_alive():
            try:
                sd.stop()
            except Exception as exc:
                print(f"Audio stop error: {exc}")
        self._is_playing.clear()

    @property
    def is_playing(self) -> bool:
        """Return True when audio is currently playing."""
        return self._is_playing.is_set()

    def play_speech(self, text: str, voice: str | None = None) -> None:
        """Generate speech from text and play it directly through speakers.

        This method creates a temporary audio file, plays it, then deletes it.
        Uses WAV format for maximum compatibility with sounddevice.

        Args:
            text: Text to speak
            voice: Voice to use (or default if None)
        """
        text = text[:2000]
        if not text or text.strip() == "":
            print("Warning: Empty text provided for speech playback")
            return
        
        voice = voice or self.default_voice
        tmp_path = None
        
        try:
            # Create temporary file for audio
            tmp = tempfile.NamedTemporaryFile(
                prefix="beacon_tts_", 
                suffix=".wav", 
                delete=False
            )
            tmp_path = tmp.name
            tmp.close()

            # Generate speech
            with self.client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",
                voice=voice,
                input=text,
                instructions="Speak in a clear, friendly, and helpful tone suitable for a blind user. Be concise but warm.",
            ) as response:
                response.stream_to_file(tmp_path)

            # Play the audio
            data, samplerate = sf.read(tmp_path, dtype="float32")
            if samplerate != 48000:
                data = librosa.resample(data.T, orig_sr=samplerate, target_sr=48000).T
                samplerate = 48000

            self.stop_playback()  # Ensure previous playback is halted

            def _playback_worker(buffer, sample_rate):
                try:
                    sd.play(buffer, sample_rate, blocking=False)
                    sd.wait()
                except Exception as playback_exc:
                    print(f"Speech playback error: {playback_exc}")
                finally:
                    with self._playback_lock:
                        self._is_playing.clear()
                        self._playback_thread = None

            playback_thread = Thread(target=_playback_worker, args=(data, samplerate), daemon=True)

            with self._playback_lock:
                self._is_playing.set()
                self._playback_thread = playback_thread
            playback_thread.start()
            
        except Exception as exc:
            print(f"Speech playback error: {exc}")
            # Don't raise - we want the app to continue even if audio fails
            
        finally:
            # Clean up the temporary file
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

if __name__ == "__main__":
    print("\a")