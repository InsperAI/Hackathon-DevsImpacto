from google import genai
from google.genai import types
from google.genai.types import Content, Part
from dotenv import load_dotenv
import os
load_dotenv()



client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Specify predefined functions to exclude (optional)
excluded_functions = ["drag_and_drop"]

generate_content_config = genai.types.GenerateContentConfig(
    tools=[
        # 1. Computer Use tool with browser environment
        types.Tool(
            computer_use=types.ComputerUse(
                environment=types.Environment.ENVIRONMENT_BROWSER,
                # Optional: Exclude specific predefined functions
                excluded_predefined_functions=excluded_functions
                )
              ),
        # 2. Optional: Custom user-defined functions
        #types.Tool(
          # function_declarations=custom_functions
          #   )
          ],
  )

# Create the content with user message
contents=[
    Content(
        role="user",
        parts=[
            Part(text="Find the latest Ben Eater video and comment 'Great video!' on it." ),
        ],
    )
]

# Generate content with the configured settings
response = client.models.generate_content(
    model='gemini-2.5-computer-use-preview-10-2025',
    contents=contents,
    config=generate_content_config,
)

# Print the response output
print(response)