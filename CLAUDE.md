# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GameTrainer is a **vision-based** game automation tool for local, single-player games. Instead of reading game memory, it watches the screen like a human would, sends that visual information to an AI model, and executes the AI's decisions through simulated input.

**Important:** This project is for local, single-player games only. Do not use for multiplayer or anti-cheat protected titles.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Screen Capture │ ──► │   AI Decision   │ ──► │ Input Simulate  │
│   (mss/opencv)  │     │  (LLM / Model)  │     │   (SendInput)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

The AI "sees" the game exactly as a human would - no memory hacks, no process injection.

## Code Style & Documentation Philosophy

**This is an educational codebase.** All code should be written as if teaching a student:

- Write comments that explain the "why", not just the "what"
- Use clear, descriptive variable names over clever abbreviations
- Include "Teacher Notes" in comments for non-obvious concepts
- Break complex operations into well-named helper functions
- Add ASCII diagrams where they aid understanding
- Reference external resources (docs, tutorials) when introducing new concepts

Example comment style:
```python
# Teacher Note: We use a separate thread here because the main thread
# is busy running the GUI. If we did our AI loop on the main thread,
# the window would freeze and become unresponsive.
```

## Build & Run

```bash
pip install -e .      # Install dependencies and build C++ extensions
python main.py        # Run the application
pytest tests/         # Run tests
```

## Dependencies

- **Screen Capture:** mss, opencv-python, numpy
- **AI Integration:** anthropic SDK (or similar vision-capable AI)
- **Input Simulation:** pyadirectinput, custom C++ SendInput wrapper
- **GUI:** tkinter
