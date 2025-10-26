# Beacon Usage Guide

## Getting Started

### First Time Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Install browser:**
   ```bash
   uvx playwright install chromium --with-deps
   ```

3. **Configure API key:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Run pre-flight check:**
   ```bash
   uv run setup_check.py
   ```

5. **Start Beacon:**
   ```bash
   uv run main.py
   ```

## Using Beacon

### Keyboard Shortcuts

- **⌘/Ctrl + R** — Start voice recording (speak your command)
- **⌘/Ctrl + S** — Stop current audio playback and immediately start listening
- **⌘/Ctrl + H** — Hear the help message
- **⌘/Ctrl + Q** — Quit Beacon

> **Tip:** Use ⌘/Ctrl + S to interrupt Beacon when it's speaking too much or you want to give a new command immediately.

### Voice Commands Reference

#### Navigation Commands
```
"Go to amazon.com"
"Open YouTube"
"Navigate to nytimes.com"
"Visit github.com"
"Go back"
"Refresh the page"
```

#### Understanding Pages
```
"What is this page?"
"Summarize this page"
"What can I do here?"
"Tell me about this page"
"What are my options?"
```

#### Performing Actions
```
"Click add to cart"
"Do number 2"              # Performs action #2 from menu
"Read the main article"
"Show me the reviews"
"Search for wireless headphones"
"Scroll down"
"Click the login button"
```

#### Form Interaction
```
"Type John Doe in the name field"
"Fill in my email"
"Select United States from the dropdown"
"Check the agree box"
```

#### Information Retrieval
```
"Read the description"
"What's the price?"
"Tell me about this product"
"Read the first result"
```

#### Help & Control
```
"Help"                     # Hear full help guide
"What can I do?"
"Commands"
"Stop"
"Quit"
```

## Example Sessions

### Shopping Example

```
User: [presses ⌘+R]
Beacon: "Listening. Please speak your command now."

User: "Go to amazon.com"
Beacon: "You said: Go to amazon.com"
Beacon: "Opening Amazon... This is a shopping homepage. You can search 
        for products, view deals, or browse categories. Available actions:
        1. Search for a product
        2. View today's deals
        3. Browse all departments
        4. Access your account
        Done. Ready for your next command."

User: [presses ⌘+R]
User: "Search for wireless headphones"
Beacon: "Searching for wireless headphones... Search results page. 
        Here are the top options:
        1. Sony WH-1000XM5 - $398
        2. Bose QuietComfort 45 - $329
        3. Apple AirPods Max - $549
        Done. Ready for your next command."

User: [presses ⌘+R]
User: "Tell me more about option 1"
Beacon: "Opening Sony WH-1000XM5 product page... This is a product page 
        for Sony WH-1000XM5 wireless headphones. Price: $398, 4.7 star 
        rating from 12,450 reviews. Key features: Industry-leading noise 
        cancellation, 30-hour battery life, premium sound quality. 
        Available actions:
        1. Add to cart
        2. Read customer reviews
        3. See technical specifications
        4. Compare with similar products
        Done. Ready for your next command."
```

### Reading News Example

```
User: [presses ⌘+R]
User: "Go to the New York Times"
Beacon: "Opening nytimes.com... This is a news homepage. Top stories:
        1. Breaking: [Headline]
        2. Politics: [Headline]
        3. Technology: [Headline]
        Available actions:
        1. Read the top story
        2. Browse sections
        3. Search articles
        Done. Ready for your next command."

User: [presses ⌘+R]
User: "Read the top story"
Beacon: "Opening article... This is a news article. Title: [Title].
        [Article summary in 2-3 sentences]. Available actions:
        1. Read full article
        2. Listen to audio version
        3. Share article
        4. Read comments
        Done. Ready for your next command."

User: [presses ⌘+R]
User: "Do 1"
Beacon: "Reading full article... [Reads article content in chunks]
        Article finished. Ready for your next command."
```

## Safety Features

Beacon will **always ask for confirmation** before:

- ✅ Submitting payment information
- ✅ Making purchases (clicking "Buy Now", "Place Order", etc.)
- ✅ Posting or publishing content
- ✅ Sending messages or emails
- ✅ Deleting anything

### Confirmation Example

```
User: "Add to cart and checkout"
Beacon: "Adding to cart... Item added. Proceeding to checkout...
        ⚠️  Confirmation required: This will proceed to payment submission.
        Say 'yes' to confirm or 'no' to cancel.
        Listening for your response."

User: "Yes"
Beacon: "Confirmed. Proceeding."
```

## Tips for Best Results

### Speaking Commands

1. **Be natural** — Beacon understands natural language, not just exact phrases
2. **Be specific** — "Click the blue login button" is better than "click button"
3. **Use numbers** — When Beacon gives you a numbered menu, you can say "Do 2" or "Do number two"
4. **One action at a time** — While Beacon can handle complex commands, breaking them into steps gives you more control

### Audio Quality

1. **Quiet environment** — Background noise can affect transcription accuracy
2. **Clear speech** — Speak clearly and at a normal pace
3. **Close to microphone** — Position yourself within good microphone range
4. **Wait for the prompt** — Let Beacon say "Listening" before you speak

### Navigation Tips

1. **Let Beacon analyze** — After navigating to a new page, Beacon will analyze it automatically
2. **Ask for help** — If you're not sure what to do, say "What can I do here?"
3. **Use the menu** — Beacon presents the most important actions as a numbered menu
4. **Go back safely** — You can always say "go back" to return to the previous page

## Troubleshooting

### Beacon doesn't hear me

- Check your microphone is connected and selected as default
- Ensure Beacon has microphone permissions (System Preferences > Security & Privacy > Microphone)
- Try increasing recording duration in `config.py` (DEFAULT_RECORDING_DURATION)
- Reduce background noise

### Keyboard shortcuts don't work

- Make sure Beacon is the active window
- Try using the alternative (Command vs Control)
- Check accessibility permissions for the terminal/Python

### Beacon is too verbose

- The TTS voice settings can be adjusted in `config.py`
- Ask Beacon to be more concise: "Be brief" or "Short answers please"

### Browser doesn't open

- Ensure Playwright is installed: `uvx playwright install chromium --with-deps`
- Check that no other process is using the browser
- Try setting BROWSER_HEADLESS=false in config.py to see what's happening

### API errors

- Verify your OpenAI API key is correct in `.env`
- Check you have sufficient API credits
- Ensure you have access to gpt-4o-transcribe and gpt-4o-mini-tts models

## Customization

### Changing the Voice

Edit `config.py`:

```python
DEFAULT_TTS_VOICE = "coral"  # Options: coral, alloy, echo, fable, onyx, nova, shimmer
```

### Adjusting Recording Duration

Edit `config.py`:

```python
DEFAULT_RECORDING_DURATION = 7.0  # Increase for longer commands
```

### Modifying the System Prompt

Edit `config.py` and customize the `SYSTEM_PROMPT` to change how Beacon behaves and communicates.

### Running Headless

Edit `config.py`:

```python
BROWSER_HEADLESS = True  # Hide the browser window
```

## Advanced Usage

### Custom Actions

You can add custom tools/actions by editing `main.py` and adding new `@tools.action()` decorated functions.

### Different Browsers

While Chromium is default, you can modify the Browser initialization in `main.py` to use Firefox or WebKit.

### Integration

Beacon's components can be used independently:
- `AudioHandler` — For any project needing transcription/TTS
- `recorder.py` — For simple microphone recording
- The agent tools — Can be imported and used in other automation scripts

## Support

For issues, questions, or contributions:
- File an issue on GitHub
- Check the README.md for additional documentation
- Review the code comments for technical details

---

**Remember:** Beacon is designed to give you control. It will always keep you informed and ask before doing anything risky. Speak naturally and let Beacon handle the complexity!
