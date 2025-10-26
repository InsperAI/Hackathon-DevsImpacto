"""Beacon - Voice-First Browser Controller for Blind Users.

Beacon understands web pages and presents them as simple spoken menus,
allowing blind users to navigate and interact through natural voice commands.
"""

import asyncio
import os
from threading import Thread, Event
from queue import Queue, Empty
import time
from dotenv import load_dotenv
from browser_use import Agent, Browser, ChatBrowserUse, Tools, ChatGoogle
from pynput import keyboard
from audio_tools import AudioHandler
import time
from config import (
    DEFAULT_RECORDING_DURATION,
    DEFAULT_TTS_VOICE,
    MAX_STEPS_PER_TASK,
    INITIAL_MAX_STEPS,
    SHORTCUTS,
    BANNER_WIDTH,
    BROWSER_KEEP_ALIVE,
    BROWSER_HEADLESS,
    SYSTEM_PROMPT,
)

load_dotenv()

# Global state for keyboard control
voice_trigger = Event()
help_trigger = Event()
stop_audio_trigger = Event()  # Cmd/Ctrl+S to stop audio playback
command_queue = Queue()


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


def keyboard_listener_thread():
    """Listen for global keyboard shortcuts using pynput."""

    listener_holder: dict[str, keyboard.GlobalHotKeys] = {}

    def trigger_voice() -> None:
        print("🎤 Voice command triggered")
        voice_trigger.set()
        return "r"

    def trigger_help() -> None:
        help_trigger.set()

    def trigger_stop_audio() -> None:
        print("🎤 Voice command triggered")
        stop_audio_trigger.set()


    def trigger_quit() -> None:
        command_queue.put("__QUIT__")
        listener = listener_holder.get("listener")
        if listener:
            listener.stop()

    hotkeys = {
        '<cmd>+r': trigger_voice,
        '<ctrl>+r': trigger_voice,
        '<cmd>+s': trigger_stop_audio,
        '<ctrl>+s': trigger_stop_audio,
        '<cmd>+h': trigger_help,
        '<ctrl>+h': trigger_help,
        '<cmd>+q': trigger_quit,
        '<ctrl>+q': trigger_quit,
    }

    listener = keyboard.GlobalHotKeys(hotkeys)
    listener_holder["listener"] = listener
    listener.start()
    listener.join()


async def handle_voice_command(audio_handler: AudioHandler) -> str | None:
    """Capture and transcribe a voice command."""

    audio_handler.stop_playback()

    try:
        command = await asyncio.to_thread(
            audio_handler.record_and_transcribe, 
            duration_seconds=DEFAULT_RECORDING_DURATION
        )
    except Exception as exc:
        print(f"Voice command failed: {exc}")
        audio_handler.play_speech("Sorry, I could not process that. Please try again.")
        return None
    
    if not command or command.strip() == "":
        print("No speech detected.")
        audio_handler.play_speech("I didn't catch that. Please try again.")
        return None
    
    print(f"Voice command: {command}")
    audio_handler.play_speech(f"You said: {command}")
    return command.strip()


async def check_for_keyboard_events(audio_handler: AudioHandler) -> str | None:
    """Check for keyboard shortcuts and return command if any."""
    if stop_audio_trigger.is_set():
        stop_audio_trigger.clear()
        was_playing = audio_handler.is_playing
        audio_handler.stop_playback()
        if was_playing:
            print("⏹️  Audio playback stopped by keyboard shortcut")
        return None
    
    if voice_trigger.is_set():
        voice_trigger.clear()
        return "r"
    
    if help_trigger.is_set():
        help_trigger.clear()
        audio_handler.play_speech(HELP_TEXT)
        print("\n" + HELP_TEXT)
        return None
    
    try:
        cmd = command_queue.get_nowait()
        return cmd
    except Empty:
        return None


async def analyze_page_and_speak(agent: Agent, audio_handler: AudioHandler):
    """Analyze the current page and present key information to the user."""
    analysis_task = """
    Analyze this web page and provide:
    1. Page type (e.g., shopping page, article, form, search results, login page)
    2. Main purpose of the page in one sentence
    3. Most important information on the page (2-3 key points)
    4. Available actions as a numbered list (up to 5 most important actions)
    
    Format your response clearly for a blind user.
    """
    
    agent.add_new_task(analysis_task)
    result = await agent.run(max_steps=5)
    
    # Extract and speak the analysis
    if result:
        audio_handler.play_speech("Page analysis complete. Here's what I found.")
        # The agent will have already generated output; we just confirm completion


async def main(audio_handler: AudioHandler):
    """Main Beacon application loop."""
    
    # Start keyboard listener thread
    listener_thread = Thread(target=keyboard_listener_thread, daemon=True)
    listener_thread.start()
    
    # Initialize browser and agent
    print("🚀 Starting Beacon browser...")
    browser = Browser(keep_alive=BROWSER_KEEP_ALIVE, headless=BROWSER_HEADLESS)
    await browser.start()
    # llm = ChatBrowserUse()
    llm = ChatGoogle(model='gemini-2.5-flash', temperature=0.2, api_key=os.getenv("GEMINI_API_KEY"))
    
    tools = Tools()
    
    # @tools.action(description="Speak an alert or information aloud to the blind user.")
    # async def speak_to_user(message: str, priority: str | None = None) -> str:
    #     """Convert the provided message into speech and play it for the user."""
    #     cleaned = message.strip() or "Attention needed."
    #     spoken_message = f"Priority {priority}. {cleaned}" if priority else cleaned
        
    #     print(f"🔊 [Beacon] {spoken_message}")
        
    #     try:
    #         await asyncio.to_thread(audio_handler.play_speech, spoken_message)
    #     except Exception as exc:
    #         print(f"Failed to voice alert: {exc}")
    #         return f"Alert printed but speech failed: {exc}"
        
    #     return f"Message delivered: {spoken_message}"
    
    @tools.action(description="Request explicit confirmation from the user before performing high-risk actions.")
    async def request_confirmation(action_description: str) -> str:
        """Ask the user to confirm a high-risk action before proceeding."""
        prompt = f"Confirmation required: {action_description}. Say 'yes' to confirm or 'no' to cancel."
        
        print(f"⚠️  {prompt}")
        await asyncio.to_thread(audio_handler.play_speech, prompt)
        
        # Get voice response
        audio_handler.play_speech("Listening for your response.")
        try:
            response = await asyncio.to_thread(
                audio_handler.record_and_transcribe, 
                duration_seconds=5.0
            )
            response_lower = response.lower().strip()
            
            if any(word in response_lower for word in ["yes", "confirm", "proceed", "do it", "go ahead"]):
                await asyncio.to_thread(audio_handler.play_speech, "Confirmed. Proceeding.")
                return "USER_CONFIRMED"
            else:
                await asyncio.to_thread(audio_handler.play_speech, "Cancelled.")
                return "USER_CANCELLED"
        except Exception as exc:
            print(f"Confirmation failed: {exc}")
            await asyncio.to_thread(audio_handler.play_speech, "Could not get confirmation. Action cancelled.")
            return "USER_CANCELLED"
    
    # @tools.action(description="Describe what you are currently doing to keep the blind user informed.")
    # async def describe_what_im_doing(description: str) -> str:
    #     """Tell the user what action or task you are currently performing.
        
    #     This keeps the user aware of what's happening and maintains engagement.
        
    #     Args:
    #         description: A brief, clear description of what you're about to do or are doing.
    #                     Examples: "Clicking the search button", "Scrolling down to see more results",
    #                     "Opening the first article", "Typing in the search box"
        
    #     Returns:
    #         Confirmation that the message was delivered.
    #     """
    #     message = f"{description}"
    #     print(f"🔧 [Action] {message}")
        
    #     try:
    #         await asyncio.to_thread(audio_handler.play_speech, message)
    #     except Exception as exc:
    #         print(f"Failed to describe action: {exc}")
    #         return f"Description printed but speech failed: {exc}"
        
    #     return f"User informed: {message}"
    
    @tools.action(description="Ask the user for help or clarification when you're unsure how to proceed.")
    async def ask_for_user_help(question: str) -> str:
        """Ask the blind user a question when you need clarification or guidance.
        
        Use this when:
        - Multiple options exist and you're unsure which to choose
        - The page is ambiguous or unclear
        - You need more context about what the user wants
        - An unexpected situation occurs
        
        Args:
            question: A clear, specific question for the user.
                     Examples: "I found three login buttons. Which one should I use?",
                     "Should I filter by price or by rating?",
                     "The page has a popup. Should I close it or interact with it?"
        
        Returns:
            The user's spoken response.
        """
        prompt = f"{question} Please speak your answer after the beep."
        print(f"❓ [Question] {question}")
        
        await asyncio.to_thread(audio_handler.play_speech, prompt)
        
        # Get voice response
        try:
            response = await asyncio.to_thread(
                audio_handler.record_and_transcribe, 
                duration_seconds=7.0
            )
            
            if not response or response.strip() == "":
                await asyncio.to_thread(audio_handler.play_speech, "I didn't catch that. I'll make my best guess.")
                return "USER_DID_NOT_RESPOND"
            
            print(f"📝 User answered: {response}")
            await asyncio.to_thread(audio_handler.play_speech, f"Got it. {response}")
            return response.strip()
            
        except Exception as exc:
            print(f"Failed to get user response: {exc}")
            await asyncio.to_thread(audio_handler.play_speech, "I couldn't hear your response. I'll proceed with my best judgment.")
            return "USER_DID_NOT_RESPOND"
    
    # Create agent with initial task
    agent = Agent(
        task="do nothing",
        browser_session=browser,
        llm=llm,
        tools=tools,
        extend_system_message=SYSTEM_PROMPT,
    )
    
    audio_handler.play_speech("Ready for your command.")
    
    # Main interaction loop
    print("\n" + "="*BANNER_WIDTH)
    print(f"Beacon is ready! Use {SHORTCUTS['voice']} to speak commands.")
    print(f"Press {SHORTCUTS['stop_audio']} to stop audio playback.")
    print(f"Press {SHORTCUTS['help']} for help.")
    print(f"Press {SHORTCUTS['quit']} to quit.")
    print("="*BANNER_WIDTH + "\n")
    
    while True:
        # Check for keyboard shortcuts
        keyboard_cmd = await check_for_keyboard_events(audio_handler)
        print
        if keyboard_cmd == "__QUIT__":
            break
        if keyboard_cmd == "r":
            nxt = await handle_voice_command(audio_handler)
        else:
            # Wait a bit and check again for keyboard events
            await asyncio.sleep(0.1)
            continue
        
        # Handle help command
        if nxt.lower() in {"help", "help me", "what can i do", "commands"}:
            audio_handler.play_speech(HELP_TEXT)
            audio_handler.play_speech("Ready for your next command.")
            continue
        
        # Handle exit commands
        if nxt.lower() in {"exit", "quit", "goodbye", "stop"}:
            break
        
        # Process the command
        print(f"\n📝 Processing: {nxt}")
        agent.add_new_task(nxt)
        
        try:
            history = await agent.run(max_steps=MAX_STEPS_PER_TASK)
            audio_handler.play_speech(history.final_result())
        except Exception as exc:
            print(f"Error executing task: {exc}")
            audio_handler.play_speech("Sorry, I encountered an error. Please try again.")
    
    # Cleanup
    print("\n🛑 Shutting down Beacon...")
    await browser.kill()


if __name__ == "__main__":
    audio_handler = AudioHandler(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        voice=DEFAULT_TTS_VOICE
    )
    
    print("\n" + "="*BANNER_WIDTH)
    print("🔷 BEACON - Voice-First Browser Controller")
    print("="*BANNER_WIDTH)
    
    audio_handler.play_speech("Welcome to Beacon, your voice-first browser assistant!")
    
    try:
        asyncio.run(main(audio_handler))
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    finally:
        audio_handler.play_speech("Shutting down. Goodbye!")
        print("👋 Beacon closed.")
