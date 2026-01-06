# GameTrainer Design Document

> **Teacher Note:** This is the high-level "what and why" document. For detailed
> implementation specifics, see `knowledge_system_design.md`.

---

> **Scope note (ethics & legality):** This project is intended for **local,
> single‑player games** (e.g., Stardew Valley–like titles) and **offline**
> experimentation on games **you own and control**. Do **not** use, distribute,
> or adapt this for multiplayer or anti‑cheat–protected titles.

---

## 1. Overview

### 1.1 Purpose

GameTrainer is a **vision-based** game automation tool that:

- **Records** gameplay videos for training (you play, it watches)
- **Learns** game mechanics by uploading videos to Claude for analysis
- **Watches** the screen like a human would (no memory reading or process injection)
- **Decides** what actions to take using fast, local rule evaluation (FREE at runtime)
- **Acts** via simulated keyboard/mouse input
- **Improves** by recording and analyzing new scenarios

```
┌─────────────────────────────────────────────────────────────────┐
│                     THE CORE PHILOSOPHY                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   "Pay once to train, play forever for free."                   │
│                                                                 │
│   TRAINING (paid, one-time):                                    │
│   ✓ Record gameplay videos while you play                       │
│   ✓ Upload videos to Claude for analysis                        │
│   ✓ Claude extracts rules, UI locations, patterns               │
│   ✓ Save training data locally                                  │
│                                                                 │
│   RUNTIME (free, forever):                                      │
│   ✓ Look at the screen (like your eyes)                         │
│   ✓ Press keys and move the mouse (like your hands)             │
│   ✓ Use local decision trees (no API calls!)                    │
│                                                                 │
│   We DON'T:                                                     │
│   ✗ Read game memory                                            │
│   ✗ Inject code into processes                                  │
│   ✗ Modify game files                                           │
│   ✗ Use kernel drivers                                          │
│   ✗ Call AI APIs during gameplay (that costs money!)            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Goals

| Goal | Description |
|------|-------------|
| **Cost-Effective** | Pay for video analysis once, run forever for free |
| **Educational** | Code is written to teach; comments explain "why" not just "what" |
| **Transparent** | Every decision can be traced to a human-readable rule |
| **Efficient** | AI used only for training (video analysis); runtime is pure local logic |
| **Safe** | Built-in limits prevent runaway behavior |
| **Maintainable** | Clean architecture, typed Python, documented interfaces |

### 1.3 Out of Scope

- Memory reading / process attachment
- Code injection of any kind
- Kernel-mode drivers
- Stealth or anti-detection techniques
- Network play or anything affecting other players

---

## 2. User Stories

### Who is this for?

A developer or hobbyist who wants to:
- Automate repetitive tasks in single-player games
- Learn about computer vision, rule engines, and AI integration
- Build a portfolio project demonstrating clean architecture

### User Stories

- **US-01:** As a user, I can point the tool at a game window and have it
  automatically learn basic mechanics from that game's wiki.

- **US-02:** As a user, I can start/stop automation with clear visual feedback
  about what the bot is "thinking" and doing.

- **US-03:** As a user, I can set safety limits (max runtime, max actions per
  minute, pause when I touch keyboard/mouse).

- **US-04:** As a user, I can review and edit the rules the system generated,
  so I understand and control its behavior.

- **US-05:** As a user, I can see a log of exceptions (times when actions didn't
  work as expected) and trigger relearning for those cases.

---

## 3. Architecture

### 3.1 System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            GAMETRAINER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   TRAINING PHASE (uses AI, one-time cost)                               │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────┐ │
│   │   Record    │───►│   Upload    │───►│   Claude    │───►│  Save   │ │
│   │  Gameplay   │    │   Video     │    │  Analyzes   │    │  Rules  │ │
│   │   Video     │    │  to Claude  │    │   Video     │    │ Locally │ │
│   └─────────────┘    └─────────────┘    └─────────────┘    └────┬────┘ │
│        FREE              PAID              PAID               FREE      │
│                                                                  │       │
│   ───────────────────────────────────────────────────────────────┼───── │
│                                                                  │       │
│   RUNTIME PHASE (no AI, fast & FREE forever)                     ▼       │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐     │
│   │   Screen    │───►│   Extract   │───►│   Evaluate Rules        │     │
│   │   Capture   │    │   State     │    │   (if/then logic)       │     │
│   └─────────────┘    └─────────────┘    └───────────┬─────────────┘     │
│        FREE              FREE                       │    FREE            │
│                                                     ▼                    │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐     │
│   │   Input     │◄───│   Verify    │◄───│   Execute Action        │     │
│   │   Simulate  │    │   Outcome   │    │                         │     │
│   └─────────────┘    └─────────────┘    └─────────────────────────┘     │
│        FREE              FREE                       FREE                 │
│                             │                                            │
│                             ▼                                            │
│                      Unexpected?                                         │
│                             │                                            │
│   ───────────────────────────┼───────────────────────────────────────── │
│                             │                                            │
│   REFINEMENT PHASE (record more video, re-analyze - optional)           │
│                             ▼                                            │
│   ┌─────────────────────────────────────────────────────────────┐       │
│   │   Record new scenario → Upload to Claude → Update rules     │       │
│   └─────────────────────────────────────────────────────────────┘       │
│                        PAID (only when needed)                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        GUI LAYER                                 │
│                     (Python / tkinter)                           │
│  • Start/Stop controls                                          │
│  • Rule viewer/editor                                           │
│  • Log display                                                  │
│  • Safety settings                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       CORE LAYER                                 │
│                        (Python)                                  │
│  • Main loop orchestration (10 Hz)                              │
│  • Knowledge base management                                    │
│  • Rule evaluation engine                                       │
│  • State extraction from frames                                 │
│  • Outcome verification                                         │
│  • Exception logging                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     INTEGRATION LAYER                            │
│                  (Python + Native Libraries)                     │
│  • Screen capture (mss → native Desktop Duplication)            │
│  • Image processing (OpenCV → native C++)                       │
│  • AI API calls (anthropic SDK → network)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      NATIVE LAYER                                │
│                    (C++ / SendInput)                             │
│  • Keyboard simulation                                          │
│  • Mouse simulation                                             │
│  • Timing-critical input                                        │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Key Components

| Component | Language | Purpose |
|-----------|----------|---------|
| `GameplayRecorder` | Python | Records gameplay videos for training |
| `VideoAnalyzer` | Python | Uploads videos to Claude for analysis |
| `KnowledgeBase` | JSON | Stores rules, entities, UI definitions (locally) |
| `ScreenCapture` | Python (mss) | Captures game window frames at runtime |
| `StateExtractor` | Python (OpenCV) | Converts pixels → game state |
| `DecisionEngine` | Python | Evaluates rules, picks actions (FREE) |
| `InputSimulator` | C++ | Executes keyboard/mouse actions |
| `OutcomeVerifier` | Python | Checks if actions worked |
| `KnowledgeHarvester` | Python | (Optional) Scrapes wikis to supplement video data |

---

## 4. Data Flow

### 4.1 One Frame Cycle (Runtime)

```
    ┌──────────────────────────────────────────────────────────────┐
    │                    SINGLE FRAME (~100ms budget)              │
    ├──────────────────────────────────────────────────────────────┤
    │                                                              │
    │  1. CAPTURE (~20ms)                                          │
    │     Screen ──► Raw frame (numpy array)                       │
    │                                                              │
    │  2. PERCEIVE (~15ms)                                         │
    │     Raw frame ──► Game state dict                            │
    │     {                                                        │
    │       "player_health": 75,                                   │
    │       "player_stamina": 30,                                  │
    │       "enemies_nearby": false                                │
    │     }                                                        │
    │                                                              │
    │  3. DECIDE (~0.1ms)                                          │
    │     Game state + Rules ──► Best matching action              │
    │     Rule "eat_when_tired" matches (stamina < 40)             │
    │                                                              │
    │  4. ACT (~5ms)                                               │
    │     Action ──► Input simulation                              │
    │     Press 'E' to open inventory                              │
    │                                                              │
    │  5. VERIFY (next frame)                                      │
    │     Did stamina increase? If not ──► Log exception           │
    │                                                              │
    └──────────────────────────────────────────────────────────────┘
```

### 4.2 Training Phase: Video Analysis (One-time Setup)

```
    User plays the game while recording
                        │
                        ▼
    ┌───────────────────────────────────────┐
    │  RECORD: Capture gameplay video       │
    │  • Play normally for 5-30 minutes     │
    │  • Demonstrate actions you want bot   │
    │    to learn (farming, combat, etc.)   │
    │  • Include edge cases (low health)    │
    │                                       │
    │  Cost: FREE (local recording)         │
    └───────────────────┬───────────────────┘
                        │
                        ▼
    ┌───────────────────────────────────────┐
    │  UPLOAD: Send video to Claude API     │
    │  • Video is sent to Claude's vision   │
    │  • Claude watches and understands     │
    │    the gameplay context               │
    │                                       │
    │  Cost: PAID (API usage)               │
    └───────────────────┬───────────────────┘
                        │
                        ▼
    ┌───────────────────────────────────────┐
    │  ANALYZE: Claude extracts knowledge   │
    │  • UI element locations & colors      │
    │  • Game state patterns                │
    │  • Action → outcome mappings          │
    │  • Decision rules (if X then Y)       │
    │                                       │
    │  Cost: PAID (API usage)               │
    └───────────────────┬───────────────────┘
                        │
                        ▼
    ┌───────────────────────────────────────┐
    │  VALIDATE: Check rule syntax          │
    │  Human reviews generated rules        │
    │  Optionally supplement with wiki data │
    │                                       │
    │  Cost: FREE                           │
    └───────────────────┬───────────────────┘
                        │
                        ▼
    ┌───────────────────────────────────────┐
    │  SAVE: Write knowledge_base.json      │
    │  Ready to use FOREVER (no more AI!)   │
    │                                       │
    │  Cost: FREE                           │
    └───────────────────────────────────────┘

    ═══════════════════════════════════════════
    TOTAL: Pay once for training, run free forever
    ═══════════════════════════════════════════
```

---

## 5. Safety Features

```
┌─────────────────────────────────────────────────────────────────┐
│                     SAFETY FIRST                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  RUNTIME LIMITS                                                  │
│  ├── Max actions per minute (default: 60)                       │
│  ├── Max runtime before auto-pause (default: 2 hours)           │
│  ├── Minimum delay between same action (default: 500ms)         │
│  └── Emergency stop hotkey (default: F12)                       │
│                                                                  │
│  USER OVERRIDE DETECTION                                         │
│  ├── Pause if user moves mouse                                  │
│  ├── Pause if user presses any key                              │
│  └── Resume only via explicit GUI action                        │
│                                                                  │
│  TRANSPARENCY                                                    │
│  ├── All decisions logged with reasoning                        │
│  ├── Rules are human-readable JSON                              │
│  └── No hidden behavior                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Project Structure

```
GameTrainer/
├── DOCUMENTS/
│   ├── game_trainer_design.md      # This file (high-level design)
│   ├── knowledge_system_design.md  # Detailed implementation spec
│   └── screen_capture_design.md    # Screen capture & recording options
│
├── src/
│   ├── python/
│   │   ├── core/
│   │   │   ├── trainer.py          # Main loop orchestration (FREE runtime)
│   │   │   ├── recorder.py         # Gameplay video recording (for training)
│   │   │   ├── training/
│   │   │   │   ├── video_analyzer.py  # Upload videos to Claude (PAID)
│   │   │   │   └── rule_generator.py  # Parse Claude's analysis to rules
│   │   │   ├── knowledge/
│   │   │   │   ├── harvester.py    # (Optional) Web scraping
│   │   │   │   └── base.py         # Knowledge base I/O
│   │   │   ├── perception/
│   │   │   │   ├── capture.py      # Screen capture (runtime)
│   │   │   │   └── extractor.py    # State extraction
│   │   │   ├── decision/
│   │   │   │   ├── engine.py       # Rule evaluation (FREE)
│   │   │   │   └── verifier.py     # Outcome checking
│   │   │   └── refinement/
│   │   │       └── learner.py      # Exception logging for retraining
│   │   │
│   │   └── gui/
│   │       ├── main_window.py      # Main application window
│   │       ├── recorder_window.py  # Recording controls & preview
│   │       ├── rule_editor.py      # View/edit rules
│   │       └── log_viewer.py       # Exception/action logs
│   │
│   └── cpp/
│       ├── input_simulator.cpp     # SendInput wrapper
│       └── input_simulator.h
│
├── profiles/                        # Game-specific profiles
│   └── stardew_valley/
│       ├── profile.yaml            # Game settings
│       ├── recordings/             # Gameplay videos (for training)
│       │   ├── raw/                # Unprocessed recordings
│       │   └── analyzed/           # Videos that have been sent to Claude
│       ├── templates/              # Template images (extracted from videos)
│       ├── regions.yaml            # UI element locations (learned from videos)
│       ├── knowledge/              # Optional wiki/guide data
│       └── rules/                  # Decision trees (generated from video analysis)
│           ├── priorities.yaml
│           └── subtrees/
│
├── tests/
│   └── python/
│
├── config.json                      # User settings
├── main.py                          # Entry point
├── setup.py                         # Build configuration
├── CMakeLists.txt                   # C++ build
└── CLAUDE.md                        # AI assistant guidance
```

---

## 7. Dependencies

### Training Phase (One-time, PAID)
| Package | Purpose |
|---------|---------|
| `opencv-python` | Video recording and frame extraction |
| `ffmpeg-python` | Video encoding/compression |
| `anthropic` | Claude API for video analysis |
| `pydantic` | JSON schema validation |

### Runtime Phase (Forever, FREE)
| Package | Purpose |
|---------|---------|
| `mss` | Fast screen capture |
| `opencv-python` | Image processing, template matching |
| `numpy` | Array operations |
| `pydantic` | JSON schema validation |

### Development
| Package | Purpose |
|---------|---------|
| `pytest` | Testing |
| `black` | Code formatting |
| `mypy` | Type checking |

### Native
| Library | Purpose |
|---------|---------|
| Windows SDK | SendInput for input simulation |
| ffmpeg | Video encoding (for recording) |

---

## 8. Success Metrics

How do we know if this project is successful?

| Metric | Target |
|--------|--------|
| **Training Phase** | |
| Video analysis cost | < $5 per game profile (initial training) |
| Rule extraction accuracy | > 80% usable rules from video |
| Training time | < 1 hour from recording to running bot |
| **Runtime Phase (FREE)** | |
| Frame processing time | < 50ms at 10 FPS |
| Rule evaluation time | < 1ms |
| Exception rate | < 5% of actions |
| API calls during gameplay | ZERO (all local) |
| **Code Quality** | |
| Code clarity | Any developer can understand in < 30 min |

---

## 9. References

- Detailed implementation: `DOCUMENTS/knowledge_system_design.md`
- Screen capture options: `DOCUMENTS/screen_capture_design.md`
- AI assistant guidance: `CLAUDE.md`

---

*Document version: 3.0 (Video-based training architecture)*
*Last updated: January 2025*
