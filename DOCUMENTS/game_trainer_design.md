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

- **Watches** the screen like a human would (no memory reading or process injection)
- **Learns** game mechanics from existing wikis and guides (knowledge bootstrapping)
- **Decides** what actions to take using fast, local rule evaluation
- **Acts** via simulated keyboard/mouse input
- **Improves** by learning from unexpected outcomes

```
┌─────────────────────────────────────────────────────────────────┐
│                     THE CORE PHILOSOPHY                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   "Play the game like a human would - by looking at the         │
│    screen and pressing buttons. Just do it faster and           │
│    without getting tired."                                      │
│                                                                 │
│   We DON'T:                                                     │
│   ✗ Read game memory                                            │
│   ✗ Inject code into processes                                  │
│   ✗ Modify game files                                           │
│   ✗ Use kernel drivers                                          │
│                                                                 │
│   We DO:                                                        │
│   ✓ Look at the screen (like your eyes)                         │
│   ✓ Press keys and move the mouse (like your hands)             │
│   ✓ Learn from documentation (like reading a guide)             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Goals

| Goal | Description |
|------|-------------|
| **Educational** | Code is written to teach; comments explain "why" not just "what" |
| **Transparent** | Every decision can be traced to a human-readable rule |
| **Efficient** | AI used sparingly (setup + exceptions); runtime is pure logic |
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
│   SETUP PHASE (uses AI, one-time)                                       │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐     │
│   │   Scrape    │───►│  LLM Parse  │───►│   Knowledge Base        │     │
│   │   Wiki      │    │  to Rules   │    │   (JSON file)           │     │
│   └─────────────┘    └─────────────┘    └───────────┬─────────────┘     │
│                                                     │                    │
│   ──────────────────────────────────────────────────┼────────────────── │
│                                                     │                    │
│   RUNTIME PHASE (no AI, fast & free)                ▼                    │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐     │
│   │   Screen    │───►│   Extract   │───►│   Evaluate Rules        │     │
│   │   Capture   │    │   State     │    │   (if/then logic)       │     │
│   └─────────────┘    └─────────────┘    └───────────┬─────────────┘     │
│                                                     │                    │
│                                                     ▼                    │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐     │
│   │   Input     │◄───│   Verify    │◄───│   Execute Action        │     │
│   │   Simulate  │    │   Outcome   │    │                         │     │
│   └─────────────┘    └─────────────┘    └─────────────────────────┘     │
│                             │                                            │
│                             ▼                                            │
│                      Unexpected?                                         │
│                             │                                            │
│   ──────────────────────────┼────────────────────────────────────────── │
│                             │                                            │
│   REFINEMENT PHASE (uses AI, occasional)                                │
│                             ▼                                            │
│   ┌─────────────────────────────────────────────────────────────┐       │
│   │   Log exception → Batch analyze → Update rules              │       │
│   └─────────────────────────────────────────────────────────────┘       │
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
| `KnowledgeHarvester` | Python | Scrapes wikis for game information |
| `KnowledgeCompiler` | Python | Uses LLM to convert text → rules |
| `KnowledgeBase` | JSON | Stores rules, entities, UI definitions |
| `ScreenCapture` | Python (mss) | Captures game window frames |
| `StateExtractor` | Python (OpenCV) | Converts pixels → game state |
| `DecisionEngine` | Python | Evaluates rules, picks actions |
| `InputSimulator` | C++ | Executes keyboard/mouse actions |
| `OutcomeVerifier` | Python | Checks if actions worked |
| `RefinementSystem` | Python | Learns from failures |

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

### 4.2 Knowledge Bootstrap (One-time Setup)

```
    User provides: Game name + Wiki URL(s)
                        │
                        ▼
    ┌───────────────────────────────────────┐
    │  HARVEST: Fetch wiki pages            │
    │  "Stardew Valley Wiki - Fishing"      │
    │  "Stardew Valley Wiki - Combat"       │
    └───────────────────┬───────────────────┘
                        │
                        ▼
    ┌───────────────────────────────────────┐
    │  COMPILE: Send to LLM with prompt     │
    │  "Extract actionable rules from       │
    │   this game documentation..."         │
    └───────────────────┬───────────────────┘
                        │
                        ▼
    ┌───────────────────────────────────────┐
    │  VALIDATE: Check rule syntax          │
    │  Human reviews generated rules        │
    └───────────────────┬───────────────────┘
                        │
                        ▼
    ┌───────────────────────────────────────┐
    │  SAVE: Write knowledge_base.json      │
    │  Ready to use forever (no more AI)    │
    └───────────────────────────────────────┘
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
│   └── screen_capture_design.md    # Screen capture options
│
├── src/
│   ├── python/
│   │   ├── core/
│   │   │   ├── trainer.py          # Main loop orchestration
│   │   │   ├── knowledge/
│   │   │   │   ├── harvester.py    # Web scraping
│   │   │   │   ├── compiler.py     # LLM parsing
│   │   │   │   └── base.py         # Knowledge base I/O
│   │   │   ├── perception/
│   │   │   │   ├── capture.py      # Screen capture
│   │   │   │   └── extractor.py    # State extraction
│   │   │   ├── decision/
│   │   │   │   ├── engine.py       # Rule evaluation
│   │   │   │   └── verifier.py     # Outcome checking
│   │   │   └── refinement/
│   │   │       └── learner.py      # Exception-based learning
│   │   │
│   │   └── gui/
│   │       ├── main_window.py      # Main application window
│   │       ├── rule_editor.py      # View/edit rules
│   │       └── log_viewer.py       # Exception/action logs
│   │
│   └── cpp/
│       ├── input_simulator.cpp     # SendInput wrapper
│       └── input_simulator.h
│
├── knowledge/                       # Generated knowledge bases
│   └── stardew_valley/
│       ├── knowledge_base.json
│       └── exceptions.log
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

### Runtime
| Package | Purpose |
|---------|---------|
| `mss` | Fast screen capture |
| `opencv-python` | Image processing, template matching |
| `numpy` | Array operations |
| `anthropic` | Claude API for knowledge compilation |
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

---

## 8. Success Metrics

How do we know if this project is successful?

| Metric | Target |
|--------|--------|
| Frame processing time | < 50ms at 10 FPS |
| Rule evaluation time | < 1ms |
| Exception rate | < 5% of actions |
| Knowledge extraction accuracy | > 80% usable rules from wiki |
| Code clarity | Any developer can understand in < 30 min |

---

## 9. References

- Detailed implementation: `DOCUMENTS/knowledge_system_design.md`
- Screen capture options: `DOCUMENTS/screen_capture_design.md`
- AI assistant guidance: `CLAUDE.md`

---

*Document version: 2.0 (Vision-based architecture)*
*Last updated: December 2024*
