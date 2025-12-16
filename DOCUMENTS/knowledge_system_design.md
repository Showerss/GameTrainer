# Knowledge-Bootstrapped Game AI Design Document

> **Teacher Note:** This document describes a "smart" approach to game automation.
> Instead of training a model from scratch (expensive) or calling an AI every frame
> (slow), we extract knowledge ONCE from the internet, convert it to fast lookup
> rules, and only use AI again when something unexpected happens.

---

## Table of Contents

1. [Philosophy & Goals](#1-philosophy--goals)
2. [System Overview](#2-system-overview)
3. [Component Deep-Dives](#3-component-deep-dives)
4. [Data Structures](#4-data-structures)
5. [Implementation Phases](#5-implementation-phases)
6. [Challenges & Mitigations](#6-challenges--mitigations)
7. [Example: Stardew Valley Fishing](#7-example-stardew-valley-fishing)

---

## 1. Philosophy & Goals

### 1.1 The Core Insight

Games are **documented**. Players write wikis, guides, and tutorials. This knowledge
represents thousands of hours of human learning - why should our bot learn from
scratch when it can read?

```
TRADITIONAL ML APPROACH:
    Bot plays 10,000 games → Slowly learns patterns → Maybe gets good

OUR APPROACH:
    Read wiki for 30 seconds → Know what humans know → Play competently immediately
    Encounter something new → Learn just that one thing → Continue
```

### 1.2 Design Goals

| Goal | Why It Matters |
|------|----------------|
| **Fast at runtime** | Rule lookup in milliseconds, not API calls in seconds |
| **Cheap to operate** | No per-request AI costs during normal play |
| **Interpretable** | Can read and understand why any decision was made |
| **Incrementally improvable** | Learn from mistakes without full retraining |
| **Offline capable** | Works without internet after initial setup |

### 1.3 When to Use This Approach

✅ **Good fit:**
- Games with wikis, guides, or documented mechanics
- Turn-based or slower-paced games
- Games with clear success/failure states
- Automation of repetitive tasks (farming, grinding)

⚠️ **Less ideal:**
- Fast-twitch competitive games (fighting games, FPS)
- Games with no documentation
- Highly emergent/procedural games with unpredictable mechanics

---

## 2. System Overview

### 2.1 The Four Phases

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SYSTEM LIFECYCLE                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐  │
│  │   HARVEST   │   │   COMPILE   │   │   EXECUTE   │   │   REFINE    │  │
│  │             │──►│             │──►│             │──►│             │  │
│  │ Scrape web  │   │ Parse into  │   │ Run rules   │   │ Learn from  │  │
│  │ for knowledge│   │ rules       │   │ in real-time│   │ exceptions  │  │
│  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘  │
│        │                 │                 │                 │           │
│        ▼                 ▼                 ▼                 ▼           │
│   Once per game    Once per game     Every frame      When needed       │
│   (uses AI)        (uses AI)         (NO AI)          (uses AI)         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           GAMETRAINER                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    KNOWLEDGE LAYER                                │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │   │
│  │  │ Web Scraper │  │ LLM Parser  │  │ Knowledge Base (JSON)   │   │   │
│  │  │             │─►│             │─►│                         │   │   │
│  │  │ Fetches     │  │ Converts    │  │ • Rules                 │   │   │
│  │  │ wiki pages  │  │ text to     │  │ • Entity definitions    │   │   │
│  │  │             │  │ structured  │  │ • Expected outcomes     │   │   │
│  │  │             │  │ rules       │  │ • Visual identifiers    │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    PERCEPTION LAYER                               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │   │
│  │  │ Screen      │  │ State       │  │ Game State Object       │   │   │
│  │  │ Capture     │─►│ Extractor   │─►│                         │   │   │
│  │  │             │  │             │  │ • player_health: 75     │   │   │
│  │  │ Raw pixels  │  │ Detect bars,│  │ • player_stamina: 20    │   │   │
│  │  │             │  │ text, icons │  │ • nearby_enemies: [...]  │   │   │
│  │  │             │  │             │  │ • inventory: [...]       │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    DECISION LAYER                                 │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │   │
│  │  │ Rule        │  │ Priority    │  │ Action Queue            │   │   │
│  │  │ Evaluator   │─►│ Resolver    │─►│                         │   │   │
│  │  │             │  │             │  │ 1. eat_food()           │   │   │
│  │  │ Which rules │  │ If multiple │  │ 2. move_to(x, y)        │   │   │
│  │  │ match?      │  │ rules match,│  │ 3. interact()           │   │   │
│  │  │             │  │ pick best   │  │                         │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    ACTION LAYER                                   │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │   │
│  │  │ Input       │  │ Outcome     │  │ Exception Logger        │   │   │
│  │  │ Simulator   │─►│ Verifier    │─►│                         │   │   │
│  │  │             │  │             │  │ "Ate food but stamina   │   │   │
│  │  │ SendInput   │  │ Did it work │  │  didn't increase.       │   │   │
│  │  │ keystrokes  │  │ as expected?│  │  Screenshot attached."  │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    REFINEMENT LAYER (Occasional)                  │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │ Exception Handler                                           │ │   │
│  │  │                                                             │ │   │
│  │  │ On failure: Send context + screenshot to LLM                │ │   │
│  │  │              Ask: "Why didn't this work? Update my rules."  │ │   │
│  │  │              Save new/modified rule to knowledge base       │ │   │
│  │  └─────────────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Deep-Dives

### 3.1 Knowledge Harvester (Web Scraper)

**Purpose:** Fetch raw knowledge from the internet.

**Sources to scrape:**
- Game-specific wikis (e.g., stardewvalleywiki.com)
- Strategy guides
- Reddit guides/FAQs
- Steam community guides

```python
# Teacher Note: We're not trying to scrape EVERYTHING. We target specific
# pages that contain actionable gameplay information.

class KnowledgeHarvester:
    """
    Fetches raw text from game wikis and guides.

    Think of this as the "reading" phase - we're gathering textbooks
    before we study them.
    """

    def __init__(self, game_name: str):
        self.game_name = game_name
        self.sources = []  # List of URLs to scrape

    def add_source(self, url: str, source_type: str):
        """
        Register a knowledge source.

        Args:
            url: The webpage to scrape
            source_type: What kind of info this contains
                        ("mechanics", "items", "enemies", "quests", etc.)
        """
        self.sources.append({"url": url, "type": source_type})

    def harvest(self) -> list[dict]:
        """
        Fetch all registered sources.

        Returns:
            List of {url, type, content} dictionaries
        """
        results = []
        for source in self.sources:
            content = self._fetch_page(source["url"])
            results.append({
                "url": source["url"],
                "type": source["type"],
                "content": content
            })
        return results
```

---

### 3.2 Knowledge Compiler (LLM Parser)

**Purpose:** Convert messy wiki text into structured, machine-readable rules.

**This is where we use AI** - but only once per game, not at runtime.

```python
# Teacher Note: This is the "expensive" part, but we only do it once.
# The LLM reads human-written guides and outputs structured JSON that
# our fast rule engine can use.

class KnowledgeCompiler:
    """
    Uses an LLM to parse raw wiki text into structured rules.

    Think of this as hiring a tutor to read textbooks and create
    flashcards for you. Expensive once, but the flashcards last forever.
    """

    SYSTEM_PROMPT = """
    You are a game knowledge extractor. Given wiki text about a game,
    extract actionable rules in this exact JSON format:

    {
        "rules": [
            {
                "id": "unique_rule_id",
                "name": "Human readable name",
                "description": "What this rule does",
                "trigger": {
                    "type": "condition|event|periodic",
                    "condition": "game_state expression that must be true"
                },
                "action": {
                    "type": "input|wait|sequence",
                    "steps": ["list", "of", "actions"]
                },
                "expected_outcome": {
                    "description": "What should happen",
                    "verification": "How to check it worked"
                },
                "priority": 1-10,
                "source": "URL where this info came from"
            }
        ],
        "entities": [
            {
                "name": "Entity name (item, enemy, NPC, etc.)",
                "visual_description": "How to identify it on screen",
                "properties": {}
            }
        ]
    }

    Be specific and actionable. If the wiki says "eat food when tired",
    convert that to a precise condition like "stamina_percent < 30".
    """

    def compile(self, raw_knowledge: list[dict]) -> dict:
        """
        Send raw wiki text to LLM for parsing.

        Args:
            raw_knowledge: List of scraped wiki pages

        Returns:
            Structured knowledge base dictionary
        """
        # Combine all raw text
        combined_text = self._prepare_text(raw_knowledge)

        # Send to LLM (this is the expensive API call)
        response = self._call_llm(combined_text)

        # Parse and validate the JSON response
        knowledge_base = self._parse_response(response)

        return knowledge_base
```

**Example Transformation:**

```
INPUT (wiki text):
    "Stamina is represented by the green bar below your health.
     When stamina runs low, your character moves slower. You can
     restore stamina by eating food or sleeping. Most foods restore
     between 25-50 stamina points."

OUTPUT (structured rule):
    {
        "id": "restore_stamina_food",
        "name": "Eat Food When Tired",
        "trigger": {
            "type": "condition",
            "condition": "player.stamina_percent < 30"
        },
        "action": {
            "type": "sequence",
            "steps": [
                "open_inventory()",
                "select_item(type='food')",
                "use_selected_item()"
            ]
        },
        "expected_outcome": {
            "description": "Stamina increases by 25-50 points",
            "verification": "player.stamina > previous_stamina"
        },
        "priority": 7
    }
```

---

### 3.3 Perception System (State Extractor)

**Purpose:** Look at the screen and extract the current game state.

**No AI needed here** - we use traditional computer vision techniques.

```python
# Teacher Note: This is the "eyes" of our system. It converts raw pixels
# into meaningful data like "health = 75%". The Knowledge Base tells us
# WHERE to look and WHAT to look for.

class StateExtractor:
    """
    Extracts game state from screen captures.

    Uses the Knowledge Base to know what to look for and where.
    For example, if the KB says "health bar is red, top-left corner",
    this class knows to look there for red pixels.
    """

    def __init__(self, knowledge_base: dict):
        self.kb = knowledge_base
        self.screen = ScreenCapture()

        # Build detectors from knowledge base
        self.detectors = self._build_detectors()

    def extract_state(self) -> dict:
        """
        Capture screen and extract current game state.

        Returns:
            Dictionary of current game state values
        """
        frame = self.screen.capture()

        state = {}
        for name, detector in self.detectors.items():
            state[name] = detector.detect(frame)

        return state

    def _build_detectors(self) -> dict:
        """
        Create detector objects based on knowledge base definitions.

        Teacher Note: The Knowledge Base tells us things like:
            "stamina_bar": {
                "location": {"x": 100, "y": 50, "width": 200, "height": 20},
                "type": "horizontal_bar",
                "color": "green"
            }

        We convert these definitions into actual detector objects.
        """
        detectors = {}

        for entity in self.kb.get("ui_elements", []):
            if entity["type"] == "horizontal_bar":
                detectors[entity["name"]] = BarDetector(
                    region=entity["location"],
                    color=entity["color"]
                )
            elif entity["type"] == "icon_presence":
                detectors[entity["name"]] = IconDetector(
                    template=entity["template_image"],
                    region=entity.get("search_region")
                )
            # ... more detector types

        return detectors
```

---

### 3.4 Decision Engine (Rule Evaluator)

**Purpose:** Given the current game state, decide what action to take.

**This is pure logic** - just checking conditions and looking up actions.

```python
# Teacher Note: This is the "brain" but it's NOT an AI brain - it's more
# like a very organized filing cabinet. We look up which rules match the
# current situation, pick the highest priority one, and do that action.

class DecisionEngine:
    """
    Evaluates rules against current game state to decide actions.

    This is intentionally simple and fast. All the "intelligence" was
    front-loaded during the knowledge compilation phase.
    """

    def __init__(self, knowledge_base: dict):
        self.rules = knowledge_base.get("rules", [])
        # Sort by priority (highest first) for faster matching
        self.rules.sort(key=lambda r: r.get("priority", 0), reverse=True)

    def decide(self, game_state: dict) -> dict | None:
        """
        Find the highest-priority rule that matches current state.

        Args:
            game_state: Current game state from StateExtractor

        Returns:
            The action to take, or None if no rules match
        """
        for rule in self.rules:
            if self._evaluate_condition(rule["trigger"]["condition"], game_state):
                return {
                    "rule_id": rule["id"],
                    "rule_name": rule["name"],
                    "action": rule["action"],
                    "expected_outcome": rule["expected_outcome"]
                }

        return None  # No rules matched - do nothing

    def _evaluate_condition(self, condition: str, state: dict) -> bool:
        """
        Evaluate a condition string against the game state.

        Teacher Note: Conditions are stored as strings like:
            "player.stamina_percent < 30"
            "enemy_count > 0 and player.health_percent > 50"

        We parse and evaluate these safely (no eval()!) using a
        simple expression parser.
        """
        # Use a safe expression evaluator (NOT Python's eval!)
        return safe_eval(condition, state)
```

---

### 3.5 Outcome Verifier & Exception Handler

**Purpose:** Check if actions worked, and learn from failures.

```python
# Teacher Note: This is crucial! We don't just blindly execute actions -
# we check if they worked. If they didn't, we log the failure so we can
# learn from it later.

class OutcomeVerifier:
    """
    Verifies that actions produced expected results.

    If an action fails, logs all relevant context for later analysis.
    """

    def __init__(self, exception_log_path: str):
        self.log_path = exception_log_path
        self.pending_verification = None

    def expect(self, expected_outcome: dict, state_before: dict):
        """
        Register an expected outcome to verify on next state update.

        Args:
            expected_outcome: What should happen (from the rule)
            state_before: Game state before the action
        """
        self.pending_verification = {
            "expected": expected_outcome,
            "state_before": state_before,
            "timestamp": time.time()
        }

    def verify(self, state_after: dict, screenshot: bytes) -> bool:
        """
        Check if the expected outcome occurred.

        Args:
            state_after: Game state after action + settling time
            screenshot: Current screen capture (for logging if failed)

        Returns:
            True if outcome matched expectations, False otherwise
        """
        if not self.pending_verification:
            return True

        expected = self.pending_verification["expected"]
        state_before = self.pending_verification["state_before"]

        # Evaluate the verification condition
        success = self._check_outcome(expected, state_before, state_after)

        if not success:
            self._log_exception(
                expected=expected,
                state_before=state_before,
                state_after=state_after,
                screenshot=screenshot
            )

        self.pending_verification = None
        return success

    def _log_exception(self, **context):
        """
        Log a failed action for later analysis.

        Teacher Note: This exception log is GOLD. It tells us exactly
        what went wrong and when. We can batch-process these logs
        periodically to update our knowledge base.
        """
        exception_entry = {
            "timestamp": time.time(),
            "expected": context["expected"],
            "state_before": context["state_before"],
            "state_after": context["state_after"],
            "screenshot_path": self._save_screenshot(context["screenshot"])
        }

        # Append to exception log
        with open(self.log_path, "a") as f:
            f.write(json.dumps(exception_entry) + "\n")
```

---

### 3.6 Refinement System (Exception Processor)

**Purpose:** Periodically process logged exceptions to improve rules.

**This uses AI** - but only when reviewing failures, not during play.

```python
# Teacher Note: This is the "learning" part. We don't learn in real-time
# (that would be slow and expensive). Instead, we batch up our failures
# and periodically ask an AI to help us understand what went wrong.

class RefinementSystem:
    """
    Processes logged exceptions to improve the knowledge base.

    Run this manually or on a schedule - NOT during gameplay.
    """

    ANALYSIS_PROMPT = """
    An automated game-playing system encountered unexpected results.

    Rule that was triggered:
    {rule_info}

    Game state BEFORE action:
    {state_before}

    Game state AFTER action:
    {state_after}

    Expected outcome:
    {expected}

    [Screenshot attached]

    Please analyze why the action didn't produce the expected result.
    Then provide ONE of the following:

    1. MODIFIED_RULE: An updated version of the rule with corrected
       conditions or actions

    2. NEW_RULE: A new rule to handle this specific case

    3. KNOWLEDGE_GAP: Information we're missing that prevents handling
       this case (e.g., "Need to know inventory contents")

    Respond in JSON format.
    """

    def process_exceptions(self, exception_log_path: str, knowledge_base: dict) -> dict:
        """
        Analyze logged exceptions and suggest improvements.

        Args:
            exception_log_path: Path to the exception log file
            knowledge_base: Current knowledge base

        Returns:
            Updated knowledge base with improvements
        """
        exceptions = self._load_exceptions(exception_log_path)

        # Group similar exceptions (don't ask about the same problem 100 times)
        grouped = self._group_similar_exceptions(exceptions)

        improvements = []
        for exception_group in grouped:
            # Pick a representative example from the group
            example = exception_group[0]

            # Ask the LLM to analyze it
            analysis = self._analyze_exception(example, knowledge_base)
            improvements.append(analysis)

        # Apply improvements to knowledge base
        updated_kb = self._apply_improvements(knowledge_base, improvements)

        return updated_kb
```

---

## 4. Data Structures

### 4.1 Knowledge Base Schema

```json
{
    "_meta": {
        "game_name": "Stardew Valley",
        "version": "1.0.0",
        "last_updated": "2024-01-15T10:30:00Z",
        "sources": [
            "https://stardewvalleywiki.com/Fishing",
            "https://stardewvalleywiki.com/Combat"
        ]
    },

    "ui_elements": [
        {
            "name": "health_bar",
            "type": "horizontal_bar",
            "location": {"x": 50, "y": 30, "width": 150, "height": 12},
            "color_full": "#00FF00",
            "color_empty": "#333333",
            "description": "Player health displayed as green bar"
        },
        {
            "name": "stamina_bar",
            "type": "horizontal_bar",
            "location": {"x": 50, "y": 45, "width": 150, "height": 12},
            "color_full": "#FFD700",
            "color_empty": "#333333",
            "description": "Player energy/stamina as yellow bar"
        }
    ],

    "rules": [
        {
            "id": "heal_when_low",
            "name": "Eat Food When Health Low",
            "description": "Consume food item to restore health when below threshold",
            "trigger": {
                "type": "condition",
                "condition": "player.health_percent < 40"
            },
            "action": {
                "type": "sequence",
                "steps": [
                    {"type": "key", "key": "e", "description": "Open inventory"},
                    {"type": "wait", "ms": 200},
                    {"type": "find_and_click", "target": "food_item"},
                    {"type": "key", "key": "e", "description": "Close inventory"}
                ]
            },
            "expected_outcome": {
                "description": "Health should increase",
                "verification": "player.health_percent > state_before.player.health_percent"
            },
            "priority": 8,
            "cooldown_ms": 5000,
            "tags": ["survival", "health"]
        }
    ],

    "entities": [
        {
            "name": "slime_green",
            "type": "enemy",
            "visual": {
                "primary_color": "#00FF00",
                "shape": "blob",
                "size_range": {"min": 20, "max": 40}
            },
            "behavior": "Bounces toward player",
            "damage": 8,
            "health": 24
        }
    ],

    "game_constants": {
        "max_health": 100,
        "max_stamina": 270,
        "inventory_slots": 36,
        "toolbar_slots": 12
    }
}
```

### 4.2 Game State Schema

```json
{
    "timestamp": 1705312200.123,
    "frame_number": 4521,

    "player": {
        "health_percent": 75,
        "health_absolute": 75,
        "stamina_percent": 45,
        "stamina_absolute": 121
    },

    "environment": {
        "time_of_day": "14:30",
        "location": "farm",
        "weather": "sunny"
    },

    "detected_entities": [
        {
            "type": "enemy",
            "name": "slime_green",
            "position": {"x": 450, "y": 320},
            "distance_to_player": 85
        }
    ],

    "active_buffs": [],
    "active_debuffs": []
}
```

### 4.3 Exception Log Entry

```json
{
    "timestamp": 1705312205.456,
    "rule_id": "heal_when_low",
    "rule_name": "Eat Food When Health Low",

    "state_before": {
        "player": {"health_percent": 35, "stamina_percent": 60}
    },

    "state_after": {
        "player": {"health_percent": 35, "stamina_percent": 60}
    },

    "expected": {
        "description": "Health should increase",
        "verification": "player.health_percent > state_before.player.health_percent"
    },

    "screenshot_path": "exceptions/2024-01-15_103005_456.png",

    "hypothesis": null,
    "resolution": null,
    "resolved": false
}
```

---

## 5. Implementation Phases

### Phase 1: Foundation (Do This First)

**Goal:** Get the basic loop working with hardcoded rules.

```
[ ] Screen capture working (mss library)
[ ] Basic state extraction (health bar detection)
[ ] Hardcoded test rules (no knowledge base yet)
[ ] Input simulation working (press keys)
[ ] Main game loop running at 10 FPS
```

**Why hardcode first?** We need to prove the perception and action systems
work before adding the complexity of parsed rules.

---

### Phase 2: Knowledge Infrastructure

**Goal:** Build the knowledge base system.

```
[ ] Define JSON schemas for rules and entities
[ ] Implement rule evaluation engine
[ ] Create exception logging system
[ ] Build outcome verification system
[ ] Test with manually-written rules
```

---

### Phase 3: Knowledge Harvesting

**Goal:** Automate knowledge extraction from the web.

```
[ ] Web scraper for target wiki(s)
[ ] LLM prompt for knowledge extraction
[ ] Parser for LLM responses
[ ] Validation for generated rules
[ ] Storage system for knowledge base
```

---

### Phase 4: Refinement Loop

**Goal:** Learn from failures automatically.

```
[ ] Exception analysis prompts
[ ] Rule update/insertion logic
[ ] Duplicate detection (don't learn same thing twice)
[ ] Manual review interface for proposed changes
[ ] Versioning for knowledge base
```

---

### Phase 5: Polish & Optimization

**Goal:** Make it production-ready.

```
[ ] Performance optimization (faster capture, caching)
[ ] Better UI element detection (OCR, template matching)
[ ] Configuration UI for adding new games
[ ] Documentation and tutorials
```

---

## 6. Challenges & Mitigations

### Challenge 1: Wiki Text is Messy

**Problem:** Wiki text includes navigation, ads, irrelevant trivia.

**Mitigation:**
- Target specific wiki sections (just "Gameplay" not whole page)
- Use LLM to filter relevant information
- Manual review of initial extraction

---

### Challenge 2: Visual Detection is Hard

**Problem:** Games don't have standardized UIs. Health bars look different
in every game.

**Mitigation:**
- Start with games that have simple, clear UIs
- Include visual descriptions in knowledge base
- Allow manual calibration of UI element positions
- Consider using template matching with provided screenshots

---

### Challenge 3: When is "Unexpected" Actually Unexpected?

**Problem:** How do we know if something went wrong vs. game randomness?

**Mitigation:**
- Define clear success/failure criteria in rules
- Use statistical thresholds (failed 3 times in a row = exception)
- Allow "unknown" outcomes that don't trigger exceptions
- Human review of exception logs before retraining

---

### Challenge 4: LLM Might Generate Bad Rules

**Problem:** The LLM could misunderstand wiki text and create wrong rules.

**Mitigation:**
- Validation layer checks rule syntax and basic logic
- "Dry run" mode that shows what rules WOULD do without executing
- Manual approval for initial knowledge base
- Exception system catches rules that don't work in practice

---

## 7. Example: Stardew Valley Fishing

Let's trace through a concrete example of how this system would learn to fish.

### 7.1 Knowledge Harvesting

**Input (from wiki):**
```
"Fishing is a skill in Stardew Valley. To fish, equip a fishing rod
and cast it into water by pressing the action button. When a fish
bites (indicated by an exclamation mark and a sound), press the
action button again to start the mini-game. In the mini-game, hold
the button to raise the green bar, release to let it fall. Keep
the fish icon inside the green bar to catch it."
```

### 7.2 Compiled Rules

```json
{
    "rules": [
        {
            "id": "fishing_cast",
            "name": "Cast Fishing Line",
            "trigger": {
                "type": "condition",
                "condition": "equipped_tool == 'fishing_rod' AND near_water AND NOT fishing_active"
            },
            "action": {
                "type": "key_hold",
                "key": "action",
                "duration_ms": 1000
            },
            "expected_outcome": {
                "verification": "fishing_bobber_visible == true"
            },
            "priority": 5
        },
        {
            "id": "fishing_hook",
            "name": "Hook Fish on Bite",
            "trigger": {
                "type": "event",
                "condition": "fish_bite_indicator_visible"
            },
            "action": {
                "type": "key_press",
                "key": "action"
            },
            "expected_outcome": {
                "verification": "fishing_minigame_active == true"
            },
            "priority": 10
        },
        {
            "id": "fishing_reel_up",
            "name": "Raise Bar in Mini-game",
            "trigger": {
                "type": "condition",
                "condition": "fishing_minigame_active AND fish_icon_y < green_bar_y"
            },
            "action": {
                "type": "key_hold",
                "key": "action",
                "duration_ms": 50
            },
            "expected_outcome": {
                "verification": "green_bar_y decreases"
            },
            "priority": 10
        }
    ]
}
```

### 7.3 Runtime Execution

```
Frame 1000: State = {fishing_active: false, near_water: true, equipped: "fishing_rod"}
            Rule match: "fishing_cast"
            Action: Hold action button for 1 second

Frame 1050: State = {fishing_active: true, bobber_visible: true}
            Outcome verified: ✓

Frame 1200: State = {fish_bite_indicator: true}
            Rule match: "fishing_hook" (priority 10!)
            Action: Press action button

Frame 1205: State = {fishing_minigame: true, fish_y: 100, bar_y: 150}
            Outcome verified: ✓
            Rule match: "fishing_reel_up" (fish above bar)
            Action: Hold action button 50ms

[... continues until fish caught or escaped ...]
```

### 7.4 Exception Example

```
Exception logged:
    Rule: "fishing_hook"
    State before: {fish_bite_indicator: true}
    State after: {fishing_minigame: false, fishing_active: false}
    Expected: fishing_minigame should be active

    Screenshot shows: Player was hit by enemy during fishing!
```

### 7.5 Refinement

LLM Analysis:
```
"The fishing attempt failed because an enemy interrupted the player.
The current rules don't account for combat during fishing.

SUGGESTED NEW RULE:
{
    "id": "fishing_interrupt_combat",
    "name": "Stop Fishing When Enemy Nearby",
    "trigger": {
        "condition": "fishing_active AND enemy_distance < 50"
    },
    "action": {
        "type": "key_press",
        "key": "escape"
    },
    "priority": 15  // Higher than fishing rules!
}
"
```

---

## Summary

This architecture lets you:

1. **Bootstrap quickly** from existing game knowledge
2. **Run efficiently** without constant AI calls
3. **Understand decisions** by reading the rules
4. **Improve automatically** by learning from failures
5. **Control costs** by limiting AI to setup and exceptions

The key insight: **Front-load the intelligence, then run simple rules fast.**

---

*Document version: 1.0*
*Last updated: [Date]*
