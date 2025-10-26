"""Beacon - Voice-First Browser Controller for Blind Users.

Refactored for simplicity and easy control flow management.
"""

import asyncio
import os
from dotenv import load_dotenv

from audio_tools import AudioHandler
from beacon_controller import BeaconController, BeaconState, AgentTask
from keyboard_handler import KeyboardHandler, InputEvent
from voice_handler import VoiceHandler
from config import (
    DEFAULT_TTS_VOICE,
    SHORTCUTS,
    BANNER_WIDTH,
)

load_dotenv()


# Help text for users
HELP_TEXT = f"""
Beacon Help Guide.

Keyboard Shortcuts:
Press {SHORTCUTS['voice']} to start voice recording.
Press {SHORTCUTS['stop_audio']} to stop current audio playback.
Press {SHORTCUTS['help']} to hear this help message.
Press {SHORTCUTS['quit']} to quit Beacon.

Voice Commands:
You can ask Beacon to:
- Navigate to websites: "Go to amazon.com" or "Open YouTube"
- Summarize the page: "What is this page?" or "Summarize"
- Perform actions: "Click add to cart" or "Do number 2"
- Read content: "Read the main article" or "Read reviews"
- Fill forms: "Type John Doe in the name field"
- Search: "Search for wireless headphones"
- Go back: "Go back" or "Previous page"

Safety Features:
Beacon will always ask for confirmation before:
- Submitting payment information
- Posting or publishing content
- Deleting anything
- Making purchases

Examples:
"Open amazon.com" - Opens Amazon
"What can I do here?" - Summarizes available actions
"Do 1" - Performs the first action from the menu
"Read more details" - Reads additional content
"Help" - Plays this help message

Remember: Beacon is here to help you browse the web efficiently.
Just speak naturally and Beacon will understand your intent.
"""


class BeaconApp:
    """Main Beacon application that orchestrates all components.
    
    This class provides a clean, easy-to-understand control flow.
    """
    
    def __init__(self):
        """Initialize the Beacon application."""
        # Initialize components
        self.audio_handler = AudioHandler(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            voice=DEFAULT_TTS_VOICE
        )
        self.controller = BeaconController(
            audio_handler=self.audio_handler,
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            verbose=True
        )
        self.keyboard = KeyboardHandler()
        self.voice = VoiceHandler(self.audio_handler)
        
        # Application state
        self.running = False
        
        # Setup callbacks for better control
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """Setup callbacks to monitor and control agent flow."""
        
        async def on_state_change(old_state: BeaconState, new_state: BeaconState):
            """Called when controller state changes."""
            print(f"🔄 State: {old_state.value} → {new_state.value}")
        
        async def on_task_start(task: AgentTask):
            """Called when a task starts executing."""
            print(f"▶️  Starting task: {task.command}")
        
        async def on_task_complete(task: AgentTask, result: str):
            """Called when a task completes successfully."""
            print(f"✅ Task completed: {task.command}")
        
        async def on_error(error: Exception):
            """Called when an error occurs."""
            print(f"❌ Error: {error}")
        
        # Attach callbacks
        self.controller.on_state_change = on_state_change
        self.controller.on_task_start = on_task_start
        self.controller.on_task_complete = on_task_complete
        self.controller.on_error = on_error
    
    async def start(self):
        """Start the Beacon application."""
        print("\n" + "="*BANNER_WIDTH)
        print("🔷 BEACON - Voice-First Browser Controller")
        print("="*BANNER_WIDTH)
        
        # Welcome message
        self.audio_handler.play_speech(
            "Welcome to Beacon, your voice-first browser assistant!"
        )
        self.keyboard.start()
        await self.controller.start()
        while (self.audio_handler.is_playing):
            await asyncio.sleep(0.1)
        # Start keyboard handler
        
        # Start controller
        
        # Ready message
        self.audio_handler.play_speech("Ready for your command.")
        
        print("\n" + "="*BANNER_WIDTH)
        print(f"Beacon is ready! Use {SHORTCUTS['voice']} to speak commands.")
        print(f"Press {SHORTCUTS['stop_audio']} to stop audio playback.")
        print(f"Press {SHORTCUTS['help']} for help.")
        print(f"Press {SHORTCUTS['quit']} to quit.")
        print("="*BANNER_WIDTH + "\n")
        
        self.running = True
    
    async def handle_help(self):
        """Handle help request."""
        print("\n" + HELP_TEXT)
        self.audio_handler.play_speech(HELP_TEXT)
    
    async def handle_voice_command(self):
        """Handle voice command input."""
        # Capture command
        command = await self.voice.capture_command()
        
        if not command:
            return
        
        # Check for built-in commands
        command_lower = command.lower()
        
        # Help commands
        if command_lower in {"help", "help me", "what can i do", "commands"}:
            await self.handle_help()
            self.audio_handler.play_speech("Ready for your next command.")
            return
        
        # Exit commands
        if command_lower in {"exit", "quit", "goodbye", "stop"}:
            self.running = False
            return
        
        # Execute command with agent
        try:
            await self.controller.execute_command(command)
        except Exception as exc:
            print(f"❌ Command execution failed: {exc}")
    
    async def run(self):
        """Main application loop."""
        await self.start()
        
        # Main event loop
        while self.running:
            # Check for keyboard events
            event = self.keyboard.get_event(timeout=None)
            
            if event == InputEvent.QUIT:
                print("👋 Quit requested")
                break
            
            elif event == InputEvent.VOICE:
                await self.handle_voice_command()
            
            elif event == InputEvent.HELP:
                await self.handle_help()
            
            elif event == InputEvent.STOP_AUDIO:
                self.voice.stop_audio()
            
            # Small delay to prevent CPU spinning
            await asyncio.sleep(0.1)
        
        # Shutdown
        await self.shutdown()
    
    async def shutdown(self):
        """Gracefully shutdown the application."""
        print("\n🛑 Shutting down Beacon...")
        
        # Stop keyboard handler
        self.keyboard.stop()
        
        # Shutdown controller
        await self.controller.shutdown()
        
        # Goodbye message
        self.audio_handler.play_speech("Shutting down. Goodbye!")
        print("👋 Beacon closed.")


async def main():
    """Main entry point."""
    app = BeaconApp()
    await app.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as exc:
        print(f"\n❌ Fatal error: {exc}")
        raise
