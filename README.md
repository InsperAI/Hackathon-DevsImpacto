# Beacon MVP

Beacon is a voice-first browsing assistant designed for blind users. It analyses the current page, explains what matters, presents a numbered action menu, and executes the selected task through an autonomous browser agent. High-risk actions (purchases, submissions, posts) always require confirmation in plain language.

## Requirements
- Python 3.13 (matches the project `pyproject.toml`).
- Google Chrome running locally (Beacon connects through the `browser-use` CDP client).
- An `OPENAI_API_KEY` with access to the text and audio models used below.
- Optional for microphone input: `sounddevice` and `numpy` (`pip install sounddevice numpy`).
- macOS users get spoken output automatically through `afplay`. On other systems install `ffplay`, `mpg123`, or `sox`'s `play` command for audio playback, otherwise transcripts are printed.

## Installation

```bash
uv sync  # or: pip install -e .
```

Ensure the virtual environment is activated (`source .venv/bin/activate` when using `uv`).

## Running Beacon

```bash
python browser-use/main.py --url https://example.com
```

Useful flags:

- `--no-voice` – disable text-to-speech output (text prompts only).
- `--mic` – enable microphone capture (requires `sounddevice` and `numpy`).
- `--analysis-model`, `--tts-model`, `--transcription-model` – override default OpenAI models.
- `--agent-steps` – cap the browser agent iterations per action (defaults to 8).
- `--load-wait` – seconds to pause after navigation before summarising.

## Workflow
1. Beacon opens the target page and collects a DOM snapshot through `browser-use`.
2. `gpt-4o-mini` summarises the page intent, highlights important data, and proposes 3–6 key actions.
3. Actions are voiced as a numbered menu (`1. Add to cart`, `2. Read reviews`, …).
4. The user responds by voice or keyboard. Beacon parses numbers, action names, or navigation commands.
5. Selected actions run through the `browser-use` agent. High-risk actions require explicit confirmation.
6. Beacon reads back the result and refreshes the summary so the user can continue.

## Limitations & Next Steps
- Microphone capture is optional; for production we would add wake-word detection and streaming STT.
- Presently the agent shares a single session; future iterations could support multi-tab workflows.
- Safety heuristics rely on model output—additional rule-based checks (e.g. detecting payment forms) would harden confirmations.
- The accessibility menu is generated from DOM text; integrating landmark roles / ARIA data would further improve prioritisation.
