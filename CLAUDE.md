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

## Two-Phase AI Strategy

The system uses a **teacher-student** approach to balance quality and performance:

### Training Phase (Expensive, Offline)
```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│   Screen    │ ──► │     LLM     │ ──► │  Training Data  │
│   Capture   │     │  (teacher)  │     │  (state→action) │
└─────────────┘     └─────────────┘     └─────────────────┘
```
- Cloud LLM (Claude, GPT-4V, etc.) labels game states with appropriate actions
- This is slow and costly, but only happens during training
- Builds the "knowledge" that gets distilled into the runtime model

### Runtime Phase (Fast, Local)
```
┌─────────────┐     ┌───────────────┐     ┌─────────────────┐
│   Screen    │ ──► │ Decision Tree │ ──► │ Input Simulate  │
│   Capture   │     │   (student)   │     │   (SendInput)   │
└─────────────┘     └───────────────┘     └─────────────────┘
```
- Lightweight decision tree runs locally, no GPU required
- Microsecond-fast decisions
- **Novel situations:** Fail gracefully (do nothing / safe default) rather than fall back to LLM

### Why This Approach?
- **Cost:** LLM only used during training, not at runtime
- **Latency:** Decision trees are nearly instant vs 1-5+ seconds for cloud LLM
- **Simplicity:** No GPU or complex inference needed in production

## Knowledge System

The AI has two sources of information:

### Vision Layer (Runtime)
- Template matching extracts game state from screen
- Detects: objects, UI elements, positions, percentages (health, energy, etc.)
- Fast, runs every frame

### Knowledge Layer (Pre-loaded)
- Wiki/guide data ingested during training
- Game calendar, events, optimal strategies
- Informs decision tree priorities based on context

```
┌─────────────────┐     ┌─────────────────┐
│  Wiki / Guides  │     │  Screen State   │
│   (knowledge)   │     │    (vision)     │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────┐
│       CONTEXT-AWARE DECISION TREE        │
│                                          │
│  Priorities shift based on:              │
│  - In-game date/season                   │
│  - Active events or festivals            │
│  - Optimal strategies from guides        │
└─────────────────────────────────────────┘
```

This allows the decision tree to answer not just "what CAN I do?" (vision) but "what SHOULD I do?" (knowledge).

## Game Profiles (Multi-Game Support)

The engine is game-agnostic. Each game is defined by a **profile** - a configuration folder containing everything game-specific:

```
┌─────────────────────────────────────────────────────────────┐
│                    CORE ENGINE (shared)                      │
│  - Screen capture                                            │
│  - Template matching system                                  │
│  - Decision tree executor                                    │
│  - Input simulation                                          │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │  Stardew   │  │  Game B    │  │  Game C    │
     │  Profile   │  │  Profile   │  │  Profile   │
     └────────────┘  └────────────┘  └────────────┘
```

### Profile Structure

```
profiles/
└── stardew_valley/
    ├── profile.yaml          # Main config (resolution, input mappings)
    ├── templates/            # Images to match on screen
    │   ├── crops/
    │   │   ├── tomato_ripe.png
    │   │   └── tomato_growing.png
    │   ├── ui/
    │   │   ├── energy_bar.png
    │   │   └── inventory_full.png
    │   └── objects/
    │       └── chest.png
    ├── regions.yaml          # Where to look for UI elements
    │   # date_display: {x: 1200, y: 10, w: 100, h: 30}
    │   # energy_bar: {x: 1250, y: 600, w: 50, h: 200}
    ├── knowledge/            # Wiki data, strategies
    │   ├── calendar.json     # Events, festivals
    │   └── crops.json        # Growth times, prices
    └── rules/                # Decision tree definitions
        ├── priorities.yaml   # Master priority list
        └── subtrees/
            ├── farming.yaml
            └── navigation.yaml
```

### Profile Components

| Component | Purpose | Example |
|-----------|---------|---------|
| **templates/** | Images to find on screen | `tomato_ripe.png` |
| **regions.yaml** | Fixed UI element locations | `energy_bar: {x: 1250, y: 600}` |
| **knowledge/** | External game data (wiki, guides) | `festivals.json` |
| **rules/** | Decision tree logic | `if energy < 20 → eat` |
| **profile.yaml** | Input mappings, resolution, settings | `harvest_key: "mouse1"` |

### Creating a New Game Profile

1. **LLM Training Phase:** Show the LLM screenshots of the new game
2. **Template Extraction:** LLM identifies key objects, you screenshot them
3. **UI Mapping:** LLM identifies where health/mana/date/etc. appear
4. **Rule Generation:** LLM suggests decision priorities based on game mechanics
5. **Knowledge Import:** Scrape or manually add wiki/guide data

The core engine code never changes - only the profile folder is swapped.

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
