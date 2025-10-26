"""Examples showing how to control and customize Beacon's agent flow.

This demonstrates the flexibility of the refactored architecture.
"""

import asyncio
import os
from dotenv import load_dotenv

from audio_tools import AudioHandler
from beacon_controller import BeaconController, BeaconState, AgentTask
from config import DEFAULT_TTS_VOICE

load_dotenv()


# Example 1: Basic usage with custom max steps
async def example_basic():
    """Basic example - control max steps per command."""
    print("\n=== Example 1: Basic Usage ===\n")
    
    audio_handler = AudioHandler(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        voice=DEFAULT_TTS_VOICE
    )
    
    controller = BeaconController(audio_handler=audio_handler)
    await controller.start()
    
    # Execute a command with custom step limit
    result = await controller.execute_command(
        "Go to google.com and tell me what you see",
        max_steps=3  # Limit to 3 steps
    )
    
    print(f"Result: {result}")
    
    await controller.shutdown()


# Example 2: Using callbacks to monitor agent flow
async def example_callbacks():
    """Example with callbacks to monitor and control flow."""
    print("\n=== Example 2: Using Callbacks ===\n")
    
    audio_handler = AudioHandler(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        voice=DEFAULT_TTS_VOICE
    )
    
    controller = BeaconController(audio_handler=audio_handler)
    
    # Track task execution
    task_log = []
    
    async def on_task_start(task: AgentTask):
        """Log when tasks start."""
        task_log.append(f"Started: {task.command}")
        print(f"📝 Task started: {task.command}")
        print(f"   Max steps: {task.max_steps}")
    
    async def on_task_complete(task: AgentTask, result: str):
        """Log when tasks complete."""
        task_log.append(f"Completed: {task.command}")
        print(f"✅ Task completed: {task.command}")
        print(f"   Result length: {len(result)} chars")
    
    async def on_state_change(old_state: BeaconState, new_state: BeaconState):
        """Monitor state changes."""
        print(f"🔄 State transition: {old_state.value} → {new_state.value}")
    
    # Attach callbacks
    controller.on_task_start = on_task_start
    controller.on_task_complete = on_task_complete
    controller.on_state_change = on_state_change
    
    await controller.start()
    
    # Execute multiple commands
    commands = [
        "Open wikipedia.org",
        "What is the main article about?",
        "Search for Python programming",
    ]
    
    for cmd in commands:
        await controller.execute_command(cmd)
        await asyncio.sleep(1)  # Small delay between commands
    
    print("\n📊 Task Log:")
    for entry in task_log:
        print(f"  - {entry}")
    
    await controller.shutdown()


# Example 3: Custom task with metadata
async def example_custom_task():
    """Example using custom AgentTask objects with metadata."""
    print("\n=== Example 3: Custom Tasks with Metadata ===\n")
    
    audio_handler = AudioHandler(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        voice=DEFAULT_TTS_VOICE
    )
    
    controller = BeaconController(audio_handler=audio_handler)
    
    # Track task metadata
    async def on_task_start(task: AgentTask):
        if task.metadata:
            print(f"📋 Task metadata: {task.metadata}")
    
    controller.on_task_start = on_task_start
    
    await controller.start()
    
    # Create custom tasks with metadata
    tasks = [
        AgentTask(
            command="Go to amazon.com",
            max_steps=2,
            metadata={"category": "navigation", "priority": "high"}
        ),
        AgentTask(
            command="Search for wireless headphones",
            max_steps=3,
            metadata={"category": "search", "user_intent": "shopping"}
        ),
        AgentTask(
            command="Read the first three results",
            max_steps=4,
            metadata={"category": "information", "detail_level": "summary"}
        ),
    ]
    
    for task in tasks:
        print(f"\n🎯 Executing: {task.command}")
        print(f"   Category: {task.metadata.get('category')}")
        await controller.execute_task(task)
    
    await controller.shutdown()


# Example 4: Conditional execution based on state
async def example_conditional_flow():
    """Example showing conditional execution based on controller state."""
    print("\n=== Example 4: Conditional Flow Control ===\n")
    
    audio_handler = AudioHandler(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        voice=DEFAULT_TTS_VOICE
    )
    
    controller = BeaconController(audio_handler=audio_handler)
    await controller.start()
    
    commands = [
        "Open reddit.com",
        "What are the top posts?",
        "Read the first post",
    ]
    
    for cmd in commands:
        # Check if controller is ready before executing
        if not controller.is_ready:
            print(f"⏳ Waiting for controller to be ready...")
            while not controller.is_ready:
                await asyncio.sleep(0.5)
        
        print(f"\n🎯 Executing: {cmd}")
        
        try:
            result = await controller.execute_command(cmd, max_steps=5)
            print(f"✅ Success! Got {len(result)} characters")
        except Exception as exc:
            print(f"❌ Failed: {exc}")
            # Controller automatically returns to ready state on error
            continue
    
    await controller.shutdown()


# Example 5: Simple sequential workflow
async def example_workflow():
    """Example of a simple sequential workflow."""
    print("\n=== Example 5: Sequential Workflow ===\n")
    
    audio_handler = AudioHandler(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        voice=DEFAULT_TTS_VOICE
    )
    
    controller = BeaconController(audio_handler=audio_handler)
    await controller.start()
    
    # Define a shopping workflow
    workflow = [
        ("Navigate to store", "Go to amazon.com", 2),
        ("Search for product", "Search for bluetooth speakers", 3),
        ("Analyze results", "What are the top 3 products and their prices?", 4),
        ("Get details", "Tell me about the first product", 3),
    ]
    
    print("🛍️  Starting shopping workflow...\n")
    
    for step_name, command, max_steps in workflow:
        print(f"\n📍 Step: {step_name}")
        print(f"   Command: {command}")
        
        try:
            result = await controller.execute_command(command, max_steps=max_steps)
            print(f"   ✅ Completed")
        except Exception as exc:
            print(f"   ❌ Failed: {exc}")
            print("   Stopping workflow due to error")
            break
    
    print("\n🏁 Workflow complete!")
    await controller.shutdown()


if __name__ == "__main__":
    # Run one of the examples (uncomment the one you want to try)
    
    # asyncio.run(example_basic())
    # asyncio.run(example_callbacks())
    # asyncio.run(example_custom_task())
    # asyncio.run(example_conditional_flow())
    asyncio.run(example_workflow())
