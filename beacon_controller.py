"""BeaconController - Main orchestrator for voice-first browser interaction.

This module provides a clean, controllable interface for managing the agent flow,
making it easy to customize behavior and understand the interaction lifecycle.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Awaitable
import os

from browser_use import Agent, Browser, ChatGoogle, Tools
from audio_tools import AudioHandler
from config import (
    SYSTEM_PROMPT,
    MAX_STEPS_PER_TASK,
    BROWSER_KEEP_ALIVE,
    BROWSER_HEADLESS,
)


class BeaconState(Enum):
    """States of the Beacon controller."""
    INITIALIZING = "initializing"
    READY = "ready"
    LISTENING = "listening"
    PROCESSING = "processing"
    EXECUTING = "executing"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"


@dataclass
class AgentTask:
    """Represents a task for the agent to execute."""
    command: str
    max_steps: int = MAX_STEPS_PER_TASK
    requires_confirmation: bool = False
    metadata: dict | None = None


class BeaconController:
    """Controls the agent flow and manages browser interaction lifecycle.
    
    This class provides a clean separation of concerns and makes it easy to:
    - Control agent execution flow
    - Add custom tools and callbacks
    - Manage state transitions
    - Handle errors gracefully
    """
    
    def __init__(
        self,
        audio_handler: AudioHandler,
        gemini_api_key: str | None = None,
        verbose: bool = True,
    ):
        """Initialize the Beacon controller.
        
        Args:
            audio_handler: AudioHandler instance for voice I/O
            gemini_api_key: API key for Gemini (reads from env if None)
            verbose: Whether to print detailed logs
        """
        self.audio_handler = audio_handler
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.verbose = verbose
        
        # Core components (initialized in start())
        self.browser: Browser | None = None
        self.agent: Agent | None = None
        self.llm = None
        self.tools: Tools | None = None
        
        # State management
        self.state = BeaconState.INITIALIZING
        self.current_task: AgentTask | None = None
        
        # Callbacks (can be customized by user)
        self.on_state_change: Callable[[BeaconState, BeaconState], Awaitable[None]] | None = None
        self.on_task_start: Callable[[AgentTask], Awaitable[None]] | None = None
        self.on_task_complete: Callable[[AgentTask, str], Awaitable[None]] | None = None
        self.on_error: Callable[[Exception], Awaitable[None]] | None = None
    
    def log(self, message: str, prefix: str = "🔷") -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(f"{prefix} {message}")
    
    async def start(self) -> None:
        """Start the browser and initialize the agent."""
        self.log("Starting Beacon browser...")
        await self._change_state(BeaconState.INITIALIZING)
        
        try:
            # Initialize browser
            self.browser = Browser(
                keep_alive=BROWSER_KEEP_ALIVE,
                headless=BROWSER_HEADLESS
            )
            await self.browser.start()
            
            # Initialize LLM
            self.llm = ChatGoogle(
                model='gemini-2.5-flash',
                temperature=0.2,
                api_key=self.gemini_api_key
            )
            
            # Setup tools
            self.tools = Tools()
            self._register_tools()
            
            # Create agent
            self.agent = Agent(
                task="do nothing",
                browser_session=self.browser,
                llm=self.llm,
                tools=self.tools,
                extend_system_message=SYSTEM_PROMPT,
            )
            
            await self._change_state(BeaconState.READY)
            self.log("Beacon is ready!", "✅")
            
        except Exception as exc:
            await self._change_state(BeaconState.ERROR)
            self.log(f"Failed to start: {exc}", "❌")
            raise
    
    def _register_tools(self) -> None:
        """Register custom tools for the agent."""
        
        @self.tools.action(
            description="Request explicit confirmation from the user before performing high-risk actions."
        )
        async def request_confirmation(action_description: str) -> str:
            """Ask the user to confirm a high-risk action before proceeding."""
            return await self._request_confirmation(action_description)
        
        @self.tools.action(
            description="Ask the user for help or clarification when you're unsure how to proceed."
        )
        async def ask_for_user_help(question: str) -> str:
            """Ask the blind user a question when you need clarification or guidance."""
            return await self._ask_user_help(question)
    
    async def _request_confirmation(self, action_description: str) -> str:
        """Internal handler for confirmation requests."""
        prompt = f"Confirmation required: {action_description}. Say 'yes' to confirm or 'no' to cancel."
        
        self.log(f"⚠️  {prompt}")
        await asyncio.to_thread(self.audio_handler.play_speech, prompt)
        
        # Get voice response
        self.audio_handler.play_speech("Listening for your response.")
        try:
            response = await asyncio.to_thread(
                self.audio_handler.record_and_transcribe,
                duration_seconds=5.0
            )
            response_lower = response.lower().strip()
            
            if any(word in response_lower for word in ["yes", "confirm", "proceed", "do it", "go ahead"]):
                await asyncio.to_thread(self.audio_handler.play_speech, "Confirmed. Proceeding.")
                return "USER_CONFIRMED"
            else:
                await asyncio.to_thread(self.audio_handler.play_speech, "Cancelled.")
                return "USER_CANCELLED"
        except Exception as exc:
            self.log(f"Confirmation failed: {exc}", "❌")
            await asyncio.to_thread(
                self.audio_handler.play_speech,
                "Could not get confirmation. Action cancelled."
            )
            return "USER_CANCELLED"
    
    async def _ask_user_help(self, question: str) -> str:
        """Internal handler for asking user questions."""
        prompt = f"{question} Please speak your answer after the beep."
        self.log(f"❓ {question}")
        
        await asyncio.to_thread(self.audio_handler.play_speech, prompt)
        while (self.audio_handler.is_playing):
            await asyncio.sleep(0.1)
        try:
            response = await asyncio.to_thread(
                self.audio_handler.record_and_transcribe,
                duration_seconds=7.0
            )
            
            if not response or response.strip() == "":
                await asyncio.to_thread(
                    self.audio_handler.play_speech,
                    "I didn't catch that. I'll make my best guess."
                )
                return "USER_DID_NOT_RESPOND"
            
            self.log(f"📝 User answered: {response}")
            await asyncio.to_thread(self.audio_handler.play_speech, f"Got it. {response}")
            return response.strip()
            
        except Exception as exc:
            self.log(f"Failed to get user response: {exc}", "❌")
            await asyncio.to_thread(
                self.audio_handler.play_speech,
                "I couldn't hear your response. I'll proceed with my best judgment."
            )
            return "USER_DID_NOT_RESPOND"
    
    async def execute_task(self, task: AgentTask) -> str:
        """Execute a task with the agent.
        
        Args:
            task: The task to execute
            
        Returns:
            The result of the task execution
        """
        if self.state not in [BeaconState.READY, BeaconState.PROCESSING]:
            raise RuntimeError(f"Cannot execute task in state: {self.state}")
        
        self.current_task = task
        await self._change_state(BeaconState.EXECUTING)
        
        # Call task start callback
        if self.on_task_start:
            await self.on_task_start(task)
        
        try:
            self.log(f"📝 Executing: {task.command}")
            
            # Add task to agent
            self.agent.add_new_task(task.command)
            
            # Execute with configured max steps
            history = await self.agent.run(max_steps=task.max_steps)
            result = history.final_result()
            
            self.log(f"✅ Task completed: {result[:100]}...")
            
            # Speak the result
            await asyncio.to_thread(self.audio_handler.play_speech, result)
            
            # Call task complete callback
            if self.on_task_complete:
                await self.on_task_complete(task, result)
            
            await self._change_state(BeaconState.READY)
            return result
            
        except Exception as exc:
            self.log(f"❌ Task failed: {exc}")
            await self._change_state(BeaconState.ERROR)
            
            if self.on_error:
                await self.on_error(exc)
            
            # Speak error to user
            await asyncio.to_thread(
                self.audio_handler.play_speech,
                "Sorry, I encountered an error. Please try again."
            )
            
            # Return to ready state
            await self._change_state(BeaconState.READY)
            raise
        finally:
            self.current_task = None
    
    async def execute_command(self, command: str, max_steps: int | None = None) -> str:
        """Execute a simple command (convenience method).
        
        Args:
            command: The command text
            max_steps: Maximum steps (uses config default if None)
            
        Returns:
            The result of the command execution
        """
        task = AgentTask(
            command=command,
            max_steps=max_steps or MAX_STEPS_PER_TASK
        )
        return await self.execute_task(task)
    
    async def _change_state(self, new_state: BeaconState) -> None:
        """Change the controller state and trigger callback if set."""
        old_state = self.state
        self.state = new_state
        
        if self.on_state_change and old_state != new_state:
            await self.on_state_change(old_state, new_state)
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the browser and clean up resources."""
        await self._change_state(BeaconState.SHUTTING_DOWN)
        self.log("Shutting down Beacon...")
        
        if self.browser:
            try:
                await self.browser.kill()
            except Exception as exc:
                self.log(f"Error during browser shutdown: {exc}", "⚠️")
        
        self.log("Beacon shutdown complete", "✅")
    
    @property
    def is_ready(self) -> bool:
        """Check if the controller is ready to accept tasks."""
        return self.state == BeaconState.READY
    
    @property
    def is_busy(self) -> bool:
        """Check if the controller is currently processing a task."""
        return self.state in [BeaconState.EXECUTING, BeaconState.PROCESSING]
