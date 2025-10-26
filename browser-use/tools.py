from browser_use.tools import Tool

@Tool()
def custom_tool(param: str) -> str:
    """Description of what this tool does."""
    return f"Result: {param}"

agent = Agent(
    task="Your task",
    llm=llm,
    browser=browser,
    use_custom_tools=[custom_tool],
)