"""Voice command handler for Beacon.

Handles voice recording, transcription, and command processing.
"""

from __future__ import annotations

import asyncio
from audio_tools import AudioHandler
from config import DEFAULT_RECORDING_DURATION


class VoiceHandler:
    """Handles voice command capture and processing.
    
    Provides a clean interface for recording and transcribing voice commands.
    """
    
    def __init__(self, audio_handler: AudioHandler):
        """Initialize the voice handler.
        
        Args:
            audio_handler: AudioHandler instance for recording and TTS
        """
        self.audio_handler = audio_handler
    
    async def capture_command(
        self,
        duration: float = DEFAULT_RECORDING_DURATION,
        confirm: bool = True
    ) -> str | None:
        """Capture and transcribe a voice command.
        
        Args:
            duration: Recording duration in seconds
            confirm: Whether to confirm the captured command to the user
            
        Returns:
            The transcribed command text, or None if capture failed
        """
        # Stop any playing audio first
        self.audio_handler.stop_playback()
        
        try:
            # Record and transcribe
            command = await asyncio.to_thread(
                self.audio_handler.record_and_transcribe,
                duration_seconds=duration
            )
            
            # Validate command
            if not command or command.strip() == "":
                print("⚠️  No speech detected")
                await self._speak("I didn't catch that. Please try again.")
                return None
            
            command = command.strip()
            print(f"🎤 Voice command: {command}")
            
            # Confirm to user if requested
            if confirm:
                await self._speak(f"You said: {command}")
            
            return command
            
        except Exception as exc:
            print(f"❌ Voice command failed: {exc}")
            await self._speak("Sorry, I could not process that. Please try again.")
            return None
    
    async def _speak(self, text: str) -> None:
        """Helper to speak text without blocking."""
        await asyncio.to_thread(self.audio_handler.play_speech, text)
    
    def stop_audio(self) -> None:
        """Stop any currently playing audio."""
        was_playing = self.audio_handler.is_playing
        self.audio_handler.stop_playback()
        if was_playing:
            print("⏹️  Audio playback stopped")
