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
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Record    │ ──► │   Upload    │ ──► │  Claude Video   │ ──► │  Training Data  │
│  Gameplay   │     │   Videos    │     │    Analysis     │     │  (state→action) │
└─────────────┘     └─────────────┘     └─────────────────┘     └─────────────────┘
```
- **Record:** Capture gameplay videos while you play (or let the bot explore)
- **Upload:** Send video clips to Claude for analysis (paid API cost)
- **Analyze:** Claude watches the video and extracts:
  - UI element locations (health bars, inventory, etc.)
  - Game state patterns (what does "low health" look like?)
  - Action mappings (what inputs achieve what results?)
  - Decision rules (when should the bot do X vs Y?)
- **Output:** Structured training data saved locally as JSON rules

### Runtime Phase (Fast, Local, FREE)
```
┌─────────────┐     ┌───────────────┐     ┌─────────────────┐
│   Screen    │ ──► │ Decision Tree │ ──► │ Input Simulate  │
│   Capture   │     │   (student)   │     │   (SendInput)   │
└─────────────┘     └───────────────┘     └─────────────────┘
```
- Lightweight decision tree runs locally, no GPU required
- Microsecond-fast decisions, **zero API costs**
- Uses the training data generated from video analysis
- **Novel situations:** Fail gracefully (do nothing / safe default) rather than fall back to LLM

### Why This Approach?
- **Cost:** Pay once for video analysis, run forever for free
- **Quality:** Claude sees actual gameplay context, not just static screenshots
- **Latency:** Decision trees are nearly instant vs 1-5+ seconds for cloud LLM
- **Simplicity:** No GPU or complex inference needed in production
- **Temporal Understanding:** Video captures sequences (animations, timing, cause-effect)

## Knowledge System

The AI has three sources of information:

### Video Analysis Layer (Training)
- Claude watches gameplay videos and extracts structured knowledge
- Identifies UI layouts, game mechanics, cause-effect relationships
- Generates rules, templates, and region definitions automatically
- **One-time cost:** Pay for video analysis, use results forever

### Vision Layer (Runtime)
- Template matching extracts game state from screen
- Uses templates and regions learned from video analysis
- Detects: objects, UI elements, positions, percentages (health, energy, etc.)
- Fast, runs every frame, **no API costs**

### Knowledge Layer (Pre-loaded)
- Wiki/guide data can supplement video analysis
- Game calendar, events, optimal strategies
- Informs decision tree priorities based on context

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Video Analysis  │     │  Wiki / Guides  │     │  Screen State   │
│  (from Claude)  │     │   (optional)    │     │    (runtime)    │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┴───────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CONTEXT-AWARE DECISION TREE                     │
│                                                                  │
│  Priorities shift based on:                                      │
│  - Current game state (detected from screen)                     │
│  - In-game date/season (if applicable)                          │
│  - Learned patterns from video analysis                         │
│  - Optimal strategies from guides                               │
└─────────────────────────────────────────────────────────────────┘
```

This allows the decision tree to answer not just "what CAN I do?" (vision) but "what SHOULD I do?" (knowledge learned from videos).

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
    ├── recordings/           # Gameplay videos for training
    │   ├── raw/              # Original recorded footage
    │   │   ├── session_001.mp4
    │   │   └── session_002.mp4
    │   └── analyzed/         # Videos that have been processed
    │       └── session_001.mp4
    ├── templates/            # Images to match on screen (extracted from videos)
    │   ├── crops/
    │   │   ├── tomato_ripe.png
    │   │   └── tomato_growing.png
    │   ├── ui/
    │   │   ├── energy_bar.png
    │   │   └── inventory_full.png
    │   └── objects/
    │       └── chest.png
    ├── regions.yaml          # Where to look for UI elements (learned from videos)
    │   # date_display: {x: 1200, y: 10, w: 100, h: 30}
    │   # energy_bar: {x: 1250, y: 600, w: 50, h: 200}
    ├── knowledge/            # Wiki data, strategies (optional supplement)
    │   ├── calendar.json     # Events, festivals
    │   └── crops.json        # Growth times, prices
    └── rules/                # Decision tree definitions (generated from video analysis)
        ├── priorities.yaml   # Master priority list
        └── subtrees/
            ├── farming.yaml
            └── navigation.yaml
```

### Profile Components

| Component | Purpose | Example |
|-----------|---------|---------|
| **recordings/** | Gameplay videos for Claude to analyze | `session_001.mp4` |
| **templates/** | Images to find on screen (auto-extracted) | `tomato_ripe.png` |
| **regions.yaml** | Fixed UI element locations (learned from video) | `energy_bar: {x: 1250, y: 600}` |
| **knowledge/** | External game data (wiki, guides) - optional | `festivals.json` |
| **rules/** | Decision tree logic (generated from video analysis) | `if energy < 20 → eat` |
| **profile.yaml** | Input mappings, resolution, settings | `harvest_key: "mouse1"` |

### Creating a New Game Profile (Video-Based Workflow)

1. **Record Gameplay:** Capture 5-30 minutes of gameplay video showing various scenarios
   - Play normally, demonstrating the actions you want the bot to learn
   - Include edge cases: low health situations, inventory management, etc.

2. **Upload to Claude:** Send video clips to Claude API for analysis
   - Claude watches the video and identifies UI elements, game states, patterns
   - **This is the only paid API cost** - everything after is free

3. **Auto-Extract Training Data:** Claude generates:
   - Template images (cropped from video frames)
   - Region definitions (where UI elements are located)
   - Decision rules (when to take which actions)
   - Action mappings (what inputs achieve what)

4. **Review & Refine:** Manually review the generated rules
   - Adjust priorities, fix any misidentifications
   - Add supplementary knowledge from wikis if needed

5. **Run Locally (Free Forever):** The bot now runs using local decision trees
   - No more API calls during gameplay
   - All knowledge is stored in the profile folder

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

- **Screen Capture & Recording:** mss, opencv-python, numpy, ffmpeg (for video encoding)
- **Video Analysis (Training):** anthropic SDK with video support
- **Input Simulation:** pyadirectinput, custom C++ SendInput wrapper
- **GUI:** tkinter

## Training vs Runtime Costs

```
┌─────────────────────────────────────────────────────────────────┐
│                     COST BREAKDOWN                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TRAINING PHASE (One-time per game):                            │
│  ├── Record gameplay .................... FREE (local)          │
│  ├── Upload video to Claude ............. PAID (API cost)       │
│  ├── Claude analyzes video .............. PAID (API cost)       │
│  └── Save training data locally ......... FREE                  │
│                                                                  │
│  RUNTIME PHASE (Forever):                                       │
│  ├── Screen capture ..................... FREE (local)          │
│  ├── Decision tree evaluation ........... FREE (local)          │
│  ├── Input simulation ................... FREE (local)          │
│  └── All gameplay ....................... FREE (no API calls)   │
│                                                                  │
│  RESULT: Pay once for training, play forever for free!          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
