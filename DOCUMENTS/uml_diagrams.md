# UML Diagrams

> **Teacher Note:** UML (Unified Modeling Language) diagrams help us visualize
> the structure and behavior of our system. These diagrams use Mermaid syntax,
> which renders automatically on GitHub and in many editors (VS Code, etc.).

---

## Table of Contents

1. [Class Diagram](#1-class-diagram)
2. [Sequence Diagrams](#2-sequence-diagrams)
3. [State Diagram](#3-state-diagram)
4. [Component Diagram](#4-component-diagram)

---

## 1. Class Diagram

> **Teacher Note:** A class diagram shows the "nouns" of our system - what
> objects exist and how they relate to each other. Arrows show relationships:
> - Solid arrow (→): "uses" or "has a reference to"
> - Diamond (◇→): "contains" or "owns"
> - Triangle (▷): "inherits from" or "implements"

### 1.1 Core System Classes

```mermaid
classDiagram
    direction TB

    %% ============================================
    %% MAIN ORCHESTRATION
    %% ============================================

    class GameTrainer {
        <<Main Orchestrator>>
        -knowledge_base: KnowledgeBase
        -screen_capture: ScreenCapture
        -state_extractor: StateExtractor
        -decision_engine: DecisionEngine
        -input_simulator: InputSimulator
        -outcome_verifier: OutcomeVerifier
        -logger: Logger
        -running: bool
        -paused: bool
        +start() void
        +stop() void
        +pause() void
        -_main_loop() void
    }

    note for GameTrainer "The 'brain' that coordinates\nall other components.\nRuns the main 10 FPS loop."

    %% ============================================
    %% KNOWLEDGE LAYER
    %% ============================================

    class KnowledgeBase {
        <<Data Store>>
        -rules: List~Rule~
        -ui_elements: List~UIElement~
        -entities: List~Entity~
        -game_constants: Dict
        +load(filepath: str) void
        +save(filepath: str) void
        +get_rules() List~Rule~
        +add_rule(rule: Rule) void
        +update_rule(rule_id: str, rule: Rule) void
    }

    class Rule {
        <<Data Class>>
        +id: str
        +name: str
        +description: str
        +trigger: Trigger
        +action: Action
        +expected_outcome: Outcome
        +priority: int
        +cooldown_ms: int
        +enabled: bool
    }

    class Trigger {
        <<Data Class>>
        +type: str
        +condition: str
    }

    class Action {
        <<Data Class>>
        +type: str
        +steps: List~ActionStep~
    }

    class Outcome {
        <<Data Class>>
        +description: str
        +verification: str
    }

    %% ============================================
    %% PERCEPTION LAYER
    %% ============================================

    class ScreenCapture {
        <<Perception>>
        -sct: mss.MSS
        -region: CaptureRegion
        +set_region(region: CaptureRegion) void
        +set_region_from_window(title: str) bool
        +capture() ndarray
        +capture_bgr() ndarray
        +close() void
    }

    class CaptureRegion {
        <<Data Class>>
        +top: int
        +left: int
        +width: int
        +height: int
        +to_mss_dict() dict
    }

    class StateExtractor {
        <<Perception>>
        -detectors: Dict~str, Detector~
        -knowledge_base: KnowledgeBase
        +extract_state(frame: ndarray) GameState
        -_build_detectors() void
    }

    class GameState {
        <<Data Class>>
        +timestamp: float
        +player: PlayerState
        +environment: EnvironmentState
        +detected_entities: List~Entity~
        +raw_values: Dict
    }

    %% ============================================
    %% DECISION LAYER
    %% ============================================

    class DecisionEngine {
        <<Decision>>
        -rules: List~Rule~
        -cooldowns: Dict~str, float~
        +decide(game_state: GameState) Decision
        -_evaluate_condition(condition: str, state: GameState) bool
        -_is_on_cooldown(rule_id: str) bool
    }

    class Decision {
        <<Data Class>>
        +rule_id: str
        +rule_name: str
        +action: Action
        +expected_outcome: Outcome
        +confidence: float
    }

    class OutcomeVerifier {
        <<Decision>>
        -pending: PendingVerification
        -exception_log_path: str
        +expect(outcome: Outcome, state_before: GameState) void
        +verify(state_after: GameState, screenshot: bytes) bool
        -_log_exception(context: dict) void
    }

    %% ============================================
    %% ACTION LAYER
    %% ============================================

    class InputSimulator {
        <<Action>>
        -lib: CDLL
        +press_key(key: str) void
        +release_key(key: str) void
        +hold_key(key: str, duration_ms: int) void
        +mouse_move(x: int, y: int) void
        +mouse_click(button: str) void
        +execute_action(action: Action) void
    }

    %% ============================================
    %% KNOWLEDGE HARVESTING (Setup Phase)
    %% ============================================

    class KnowledgeHarvester {
        <<Setup>>
        -sources: List~Source~
        +add_source(url: str, type: str) void
        +harvest() List~RawContent~
    }

    class KnowledgeCompiler {
        <<Setup>>
        -llm_client: AnthropicClient
        +compile(raw_content: List~RawContent~) KnowledgeBase
        -_build_prompt(content: str) str
        -_parse_response(response: str) dict
    }

    %% ============================================
    %% REFINEMENT (Exception Learning)
    %% ============================================

    class RefinementSystem {
        <<Learning>>
        -llm_client: AnthropicClient
        +process_exceptions(log_path: str, kb: KnowledgeBase) KnowledgeBase
        -_analyze_exception(exception: dict) dict
        -_apply_improvements(kb: KnowledgeBase, improvements: List) KnowledgeBase
    }

    %% ============================================
    %% RELATIONSHIPS
    %% ============================================

    GameTrainer *-- KnowledgeBase : owns
    GameTrainer *-- ScreenCapture : owns
    GameTrainer *-- StateExtractor : owns
    GameTrainer *-- DecisionEngine : owns
    GameTrainer *-- InputSimulator : owns
    GameTrainer *-- OutcomeVerifier : owns

    KnowledgeBase *-- Rule : contains many
    Rule *-- Trigger : has
    Rule *-- Action : has
    Rule *-- Outcome : has

    ScreenCapture *-- CaptureRegion : uses

    StateExtractor --> KnowledgeBase : reads from
    StateExtractor ..> GameState : produces

    DecisionEngine --> KnowledgeBase : reads rules from
    DecisionEngine ..> Decision : produces

    OutcomeVerifier ..> RefinementSystem : triggers on failure

    KnowledgeHarvester ..> KnowledgeCompiler : feeds into
    KnowledgeCompiler ..> KnowledgeBase : produces

    RefinementSystem --> KnowledgeBase : updates
```

### 1.2 Class Relationship Legend

```
┌─────────────────────────────────────────────────────────────────┐
│                    RELATIONSHIP TYPES                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  A *-- B    "A owns/contains B" (composition)                  │
│             If A is destroyed, B is destroyed too              │
│             Example: GameTrainer owns ScreenCapture            │
│                                                                 │
│  A --> B    "A uses/references B" (association)                │
│             A knows about B but doesn't own it                 │
│             Example: StateExtractor reads from KnowledgeBase   │
│                                                                 │
│  A ..> B    "A produces/creates B" (dependency)                │
│             A creates instances of B                           │
│             Example: DecisionEngine produces Decision          │
│                                                                 │
│  A --|> B   "A inherits from B" (inheritance)                  │
│             A is a specialized version of B                    │
│             (Not used much in our design - prefer composition) │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Sequence Diagrams

> **Teacher Note:** Sequence diagrams show the "verbs" of our system - what
> happens over time. They show messages passing between objects from top to
> bottom. Time flows downward.

### 2.1 Runtime Loop (Single Frame)

```mermaid
sequenceDiagram
    autonumber
    participant GT as GameTrainer
    participant SC as ScreenCapture
    participant SE as StateExtractor
    participant DE as DecisionEngine
    participant OV as OutcomeVerifier
    participant IS as InputSimulator

    Note over GT: Main loop runs at 10 FPS<br/>(every 100ms)

    loop Every Frame (100ms budget)

        %% CAPTURE PHASE
        rect rgb(200, 230, 200)
            Note over GT,SC: PHASE 1: CAPTURE (~20ms)
            GT->>SC: capture_bgr()
            SC-->>GT: frame (numpy array)
        end

        %% PERCEIVE PHASE
        rect rgb(200, 200, 230)
            Note over GT,SE: PHASE 2: PERCEIVE (~15ms)
            GT->>SE: extract_state(frame)
            SE->>SE: detect UI elements
            SE->>SE: detect entities
            SE-->>GT: game_state
        end

        %% VERIFY PREVIOUS ACTION
        rect rgb(230, 230, 200)
            Note over GT,OV: PHASE 3: VERIFY PREVIOUS (~1ms)
            GT->>OV: verify(game_state, screenshot)
            alt Outcome matches expected
                OV-->>GT: true
            else Outcome unexpected
                OV->>OV: log_exception()
                OV-->>GT: false
            end
        end

        %% DECIDE PHASE
        rect rgb(230, 200, 200)
            Note over GT,DE: PHASE 4: DECIDE (~0.1ms)
            GT->>DE: decide(game_state)
            DE->>DE: evaluate rules
            DE->>DE: check cooldowns
            alt Rule matches
                DE-->>GT: decision (action to take)
            else No rule matches
                DE-->>GT: null (do nothing)
            end
        end

        %% ACT PHASE
        rect rgb(200, 230, 230)
            Note over GT,IS: PHASE 5: ACT (~5ms)
            opt If decision is not null
                GT->>OV: expect(outcome, game_state)
                GT->>IS: execute_action(decision.action)
                IS->>IS: SendInput (key/mouse)
                IS-->>GT: done
            end
        end

        Note over GT: Sleep remaining time<br/>to maintain 10 FPS

    end
```

### 2.2 Knowledge Bootstrap (Setup Phase)

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant KH as KnowledgeHarvester
    participant KC as KnowledgeCompiler
    participant LLM as Claude API
    participant KB as KnowledgeBase

    Note over U,KB: ONE-TIME SETUP<br/>(Run once per game)

    U->>KH: add_source("stardewwiki.com/Fishing")
    U->>KH: add_source("stardewwiki.com/Combat")

    U->>KH: harvest()

    rect rgb(200, 230, 200)
        Note over KH: HARVEST PHASE
        loop For each source
            KH->>KH: fetch webpage
            KH->>KH: extract text content
        end
        KH-->>KC: raw_content[]
    end

    rect rgb(200, 200, 230)
        Note over KC,LLM: COMPILE PHASE (AI Used Here)
        KC->>KC: build_prompt(raw_content)
        KC->>LLM: "Extract rules from this wiki text..."
        Note over LLM: LLM analyzes text<br/>Extracts actionable rules<br/>Structures as JSON
        LLM-->>KC: structured rules JSON
        KC->>KC: parse and validate response
    end

    rect rgb(230, 230, 200)
        Note over KC,KB: SAVE PHASE
        KC->>KB: create new KnowledgeBase
        KC->>KB: add rules, entities, UI definitions
        KB->>KB: save("knowledge_base.json")
    end

    KB-->>U: Ready to use!

    Note over U,KB: Knowledge base is now saved.<br/>AI is NOT needed during gameplay.
```

### 2.3 Exception-Based Learning (Refinement Phase)

```mermaid
sequenceDiagram
    autonumber
    participant OV as OutcomeVerifier
    participant LOG as Exception Log
    participant RS as RefinementSystem
    participant LLM as Claude API
    participant KB as KnowledgeBase

    Note over OV,KB: TRIGGERED BY FAILURES<br/>(Run periodically or manually)

    rect rgb(255, 220, 220)
        Note over OV,LOG: During Runtime - Exception Logged
        OV->>OV: Action didn't produce expected result
        OV->>LOG: append exception entry
        Note over LOG: {rule_id, state_before,<br/>state_after, screenshot}
    end

    Note over RS: Later (batch processing)...

    rect rgb(200, 230, 200)
        Note over RS,LOG: LOAD EXCEPTIONS
        RS->>LOG: read all exceptions
        RS->>RS: group similar exceptions
        LOG-->>RS: exception_groups[]
    end

    rect rgb(200, 200, 230)
        Note over RS,LLM: ANALYZE (AI Used Here)
        loop For each exception group
            RS->>LLM: "Why did this rule fail?"
            Note over LLM: Analyzes context<br/>Suggests fix
            LLM-->>RS: analysis + suggested fix
        end
    end

    rect rgb(230, 230, 200)
        Note over RS,KB: APPLY IMPROVEMENTS
        RS->>KB: update_rule() or add_rule()
        KB->>KB: save updated knowledge base
    end

    KB-->>RS: Knowledge base improved!

    Note over OV,KB: System now handles<br/>this case correctly
```

### 2.4 Sequence Diagram Legend

```
┌─────────────────────────────────────────────────────────────────┐
│                    SEQUENCE DIAGRAM SYMBOLS                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ─────>>   Synchronous message (caller waits for response)     │
│                                                                 │
│  ─────>    Asynchronous message (caller doesn't wait)          │
│                                                                 │
│  --──>>    Return message (response to a call)                 │
│                                                                 │
│  rect      Grouped actions (phases, transactions)              │
│                                                                 │
│  loop      Repeated actions                                    │
│                                                                 │
│  alt/else  Conditional branching                               │
│                                                                 │
│  opt       Optional actions (may or may not happen)            │
│                                                                 │
│  Note      Explanatory comment                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. State Diagram

> **Teacher Note:** State diagrams show the different "modes" an object can
> be in and what causes transitions between them. This is useful for
> understanding the GameTrainer's lifecycle.

### 3.1 GameTrainer States

```mermaid
stateDiagram-v2
    [*] --> Idle: Application starts

    Idle --> Initializing: start()
    note right of Idle: Waiting for user\nto press Start

    Initializing --> Running: Initialization successful
    Initializing --> Error: Initialization failed
    note right of Initializing: Loading knowledge base\nSetting up screen capture\nFinding game window

    Running --> Paused: pause() or user input detected
    Running --> Idle: stop()
    Running --> Error: Unrecoverable error
    note right of Running: Main loop active\nProcessing frames\nMaking decisions

    Paused --> Running: resume()
    Paused --> Idle: stop()
    note right of Paused: Loop suspended\nState preserved\nWaiting for resume

    Error --> Idle: User acknowledges error
    note right of Error: Error displayed\nLogs saved\nCleanup performed

    Idle --> [*]: Application closes
```

### 3.2 Rule Evaluation States

```mermaid
stateDiagram-v2
    [*] --> Evaluating: New frame received

    Evaluating --> NoMatch: No conditions met
    Evaluating --> Matched: Condition met

    Matched --> OnCooldown: Rule recently fired
    Matched --> Ready: Cooldown expired

    OnCooldown --> [*]: Skip this rule

    NoMatch --> [*]: Try next rule

    Ready --> Executing: Highest priority
    Ready --> Skipped: Lower priority rule wins

    Skipped --> [*]: Another rule chosen

    Executing --> Verifying: Action completed
    note right of Executing: InputSimulator\nexecutes action

    Verifying --> Success: Outcome matched
    Verifying --> Failed: Outcome unexpected

    Success --> [*]: Rule worked!
    note right of Success: Reset cooldown\nLog success

    Failed --> [*]: Log exception
    note right of Failed: Save context\nfor learning
```

---

## 4. Component Diagram

> **Teacher Note:** Component diagrams show the high-level "boxes" of our
> system and how they communicate. This is a zoomed-out view compared to
> class diagrams.

### 4.1 System Components

```mermaid
flowchart TB
    subgraph GUI ["GUI Layer"]
        MW[Main Window]
        RE[Rule Editor]
        LV[Log Viewer]
    end

    subgraph Core ["Core Layer"]
        GT[GameTrainer<br/>Orchestrator]

        subgraph Perception ["Perception"]
            SC[Screen<br/>Capture]
            SE[State<br/>Extractor]
        end

        subgraph Decision ["Decision"]
            DE[Decision<br/>Engine]
            OV[Outcome<br/>Verifier]
        end

        subgraph Knowledge ["Knowledge"]
            KB[(Knowledge<br/>Base)]
            KH[Knowledge<br/>Harvester]
            KC[Knowledge<br/>Compiler]
            RS[Refinement<br/>System]
        end
    end

    subgraph Native ["Native Layer"]
        IS[Input<br/>Simulator<br/>C++]
    end

    subgraph External ["External Services"]
        LLM[Claude API]
        WEB[Game Wikis]
    end

    subgraph OS ["Operating System"]
        SCR[Screen<br/>Buffer]
        INP[Input<br/>System]
    end

    %% GUI to Core
    MW --> GT
    RE --> KB
    LV --> GT

    %% Core connections
    GT --> SC
    GT --> SE
    GT --> DE
    GT --> OV
    GT --> IS

    SC --> SE
    SE --> DE
    DE --> OV
    KB --> SE
    KB --> DE

    %% Knowledge flow
    KH --> KC
    KC --> KB
    OV --> RS
    RS --> KB

    %% External connections
    KH -.-> WEB
    KC -.-> LLM
    RS -.-> LLM

    %% OS connections
    SC -.-> SCR
    IS -.-> INP

    %% Styling
    style GUI fill:#e1f5fe
    style Core fill:#fff3e0
    style Native fill:#fce4ec
    style External fill:#f3e5f5
    style OS fill:#e8f5e9
```

### 4.2 Data Flow Overview

```mermaid
flowchart LR
    subgraph Input
        S[Screen]
        W[Wiki]
    end

    subgraph Process
        C[Capture]
        E[Extract]
        D[Decide]
        A[Act]
    end

    subgraph Output
        K[Keyboard]
        M[Mouse]
    end

    subgraph Learn
        L[Exceptions]
        R[Refine]
    end

    S --> C --> E --> D --> A --> K
    A --> M
    W -.->|one-time| D
    D -->|failures| L --> R -.->|update| D

    style Input fill:#c8e6c9
    style Process fill:#fff9c4
    style Output fill:#ffccbc
    style Learn fill:#e1bee7
```

---

## 5. How to View These Diagrams

### 5.1 GitHub

GitHub automatically renders Mermaid diagrams in markdown files. Just push
this file and view it on GitHub.

### 5.2 VS Code

Install the "Markdown Preview Mermaid Support" extension:
1. Open Extensions (Ctrl+Shift+X)
2. Search "Mermaid"
3. Install "Markdown Preview Mermaid Support"
4. Open this file and press Ctrl+Shift+V for preview

### 5.3 Online Editor

Copy any diagram code to: https://mermaid.live/

### 5.4 Export to Image

Use the Mermaid CLI or online editor to export as PNG/SVG:
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i uml_diagrams.md -o diagrams.png
```

---

## 6. Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                    GAMETRAINER ARCHITECTURE                     │
│                       QUICK REFERENCE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SETUP (one-time, uses AI):                                    │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐                       │
│  │ Harvest │──►│ Compile │──►│  Save   │                       │
│  │  Wiki   │   │  Rules  │   │   KB    │                       │
│  └─────────┘   └─────────┘   └─────────┘                       │
│                                                                 │
│  RUNTIME (fast, no AI):                                        │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐        │
│  │ Capture │──►│ Extract │──►│ Decide  │──►│  Act    │        │
│  │  Frame  │   │  State  │   │  Rule   │   │  Input  │        │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘        │
│                                  │              │               │
│                                  │              ▼               │
│                                  │         ┌─────────┐         │
│                                  └────────►│ Verify  │         │
│                                            │ Outcome │         │
│                                            └─────────┘         │
│                                                 │               │
│  LEARNING (occasional, uses AI):               │               │
│                                                 ▼               │
│                              ┌─────────┐   ┌─────────┐         │
│                              │ Analyze │◄──│  Log    │         │
│                              │ Failure │   │ Exception│        │
│                              └─────────┘   └─────────┘         │
│                                  │                              │
│                                  ▼                              │
│                              Update KB                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

*Document version: 1.0*
*Last updated: December 2024*
