"""Keyboard input handler for Beacon.

Manages keyboard shortcuts and input events in a clean, reusable way.
"""

from __future__ import annotations

from threading import Thread, Event
from queue import Queue, Empty
from typing import Callable
from pynput import keyboard


class InputEvent:
    """Represents an input event from keyboard or other sources."""
    VOICE = "voice"
    HELP = "help"
    STOP_AUDIO = "stop_audio"
    QUIT = "quit"


class KeyboardHandler:
    """Handles keyboard shortcuts and input events for Beacon.
    
    Provides a clean interface for registering shortcuts and handling events.
    """
    
    def __init__(self):
        """Initialize the keyboard handler."""
        self.event_queue = Queue()
        self._listener_thread: Thread | None = None
        self._listener: keyboard.GlobalHotKeys | None = None
        self._running = False
        
        # Event triggers
        self._triggers = {
            InputEvent.VOICE: Event(),
            InputEvent.HELP: Event(),
            InputEvent.STOP_AUDIO: Event(),
            InputEvent.QUIT: Event(),
        }
    
    def start(self) -> None:
        """Start listening for keyboard shortcuts."""
        if self._running:
            return
        
        self._running = True
        self._listener_thread = Thread(target=self._listen, daemon=True)
        self._listener_thread.start()
    
    def stop(self) -> None:
        """Stop listening for keyboard shortcuts."""
        self._running = False
        if self._listener:
            self._listener.stop()
    
    def _listen(self) -> None:
        """Internal method to listen for keyboard shortcuts."""
        
        def make_trigger_handler(event_type: str) -> Callable[[], None]:
            """Create a handler function for a specific event type."""
            def handler():
                self._triggers[event_type].set()
                self.event_queue.put(event_type)
            return handler
        
        # Define hotkey mappings
        hotkeys = {
            '<cmd>+r': make_trigger_handler(InputEvent.VOICE),
            '<ctrl>+r': make_trigger_handler(InputEvent.VOICE),
            '<cmd>+s': make_trigger_handler(InputEvent.STOP_AUDIO),
            '<ctrl>+s': make_trigger_handler(InputEvent.STOP_AUDIO),
            '<cmd>+h': make_trigger_handler(InputEvent.HELP),
            '<ctrl>+h': make_trigger_handler(InputEvent.HELP),
            '<cmd>+q': make_trigger_handler(InputEvent.QUIT),
            '<ctrl>+q': make_trigger_handler(InputEvent.QUIT),
        }
        
        self._listener = keyboard.GlobalHotKeys(hotkeys)
        self._listener.start()
        self._listener.join()
    
    def get_event(self, timeout: float | None = None) -> str | None:
        """Get the next input event from the queue.
        
        Args:
            timeout: How long to wait for an event (None = don't wait)
            
        Returns:
            Event type string or None if no event available
        """
        try:
            if timeout is None:
                return self.event_queue.get_nowait()
            else:
                return self.event_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def check_event(self, event_type: str) -> bool:
        """Check if a specific event type has been triggered.
        
        Args:
            event_type: The event type to check
            
        Returns:
            True if the event was triggered, False otherwise
        """
        trigger = self._triggers.get(event_type)
        if trigger and trigger.is_set():
            trigger.clear()
            return True
        return False
    
    def clear_events(self) -> None:
        """Clear all pending events from the queue."""
        while not self.event_queue.empty():
            try:
                self.event_queue.get_nowait()
            except Empty:
                break
