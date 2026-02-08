# GameTrainer - Project Context

> **Last Updated**: 2026-02-01  
> **Current Phase**: Initial Setup & Documentation

## Project State

### What Exists
Based on conversation history, the project has:
- Python main menu code
- C++ AI/CV code components
- Some level of integration between Python and C++

### What's Being Built
- Comprehensive documentation system for learning-focused development
- Structured architecture and design documentation
- Task tracking and thought process documentation

### Recent Changes
- **2026-02-01**: Created foundational documentation structure
  - Added `.agent/README.md` with AI assistant guidelines
  - Created `architecture.md` with high-level system design
  - Created `design.md` with detailed implementation design
  - Initialized `context.md` (this file)
  - Will create `tasks.md` for ongoing task tracking

## Development Environment

### Technology Stack
- **Python**: Version TBD (recommend 3.10+)
- **C++**: Version TBD (recommend C++17 or later)
- **Build System**: TBD (CMake recommended)
- **Testing**: 
  - Python: unittest or pytest
  - C++: Google Test (gtest) recommended

### Dependencies

#### Python Dependencies (Estimated)
```
# To be confirmed based on existing code
ctypes          # C++ integration (built-in)
dataclasses     # Configuration (built-in for 3.7+)
typing          # Type hints (built-in)
# Potentially:
# - pybind11 (if switching from ctypes)
# - pytest (testing)
# - black (code formatting)
```

#### C++ Dependencies (Estimated)
```
# To be confirmed based on existing code
# Potentially:
# - OpenCV (computer vision)
# - Windows API / X11 (screen capture, input)
# - Google Test (testing)
```

### Development Setup
*To be documented after reviewing existing code*

```bash
# Expected setup process:
# 1. Clone repository
# 2. Install Python dependencies: pip install -r requirements.txt
# 3. Build C++ modules: mkdir build && cd build && cmake .. && make
# 4. Run tests: pytest tests/ && ./build/run_tests
# 5. Run application: python main.py
```

## Active Problems & Focus Areas

### Current Focus
1. **Documentation Infrastructure**: Establishing learning-focused documentation standards
2. **Code Review**: Need to review existing Python and C++ code to understand current state
3. **Architecture Validation**: Verify that proposed architecture matches existing implementation

### Known Issues
*To be populated after code review*

### Technical Debt
*To be populated as development progresses*

## Design Decisions Log

### 2026-02-01: Documentation Structure
**Decision**: Create four core documentation files (architecture.md, design.md, context.md, tasks.md)

**Rationale**: 
- Separates concerns (high-level vs detailed, current state vs plans)
- Provides clear structure for any AI assistant to understand project
- Supports learning goals by documenting "why" behind decisions

**Alternatives Considered**:
- Single README.md: Too monolithic, hard to navigate
- Wiki-style docs: Overkill for single-developer project
- Code comments only: Insufficient for architectural understanding

**Trade-offs**:
- ✅ Clear organization, easy to find information
- ✅ Supports learning and onboarding
- ❌ Requires discipline to keep updated
- ❌ Initial overhead to create

---

### 2026-02-01: AI Assistant Guidelines
**Decision**: Create explicit guidelines for AI assistants in `.agent/README.md`

**Rationale**:
- Ensures consistent experience across different AI tools (Claude, Gemini, Codex)
- Sets expectations for learning-focused interactions
- Encourages constructive criticism and deep explanations

**Key Principles**:
- Challenge suboptimal design choices
- Explain "why" not just "what"
- Relate concepts to interviews and real-world scenarios
- Maintain living documentation

---

## Project Goals & Learning Objectives

### Primary Goal
Build a functional game training assistant that demonstrates production-quality architecture and design patterns.

### Learning Objectives
1. **Architecture**: Understand how to design multi-language systems with clear boundaries
2. **Design Patterns**: Apply patterns appropriately (Strategy, Facade, Command, etc.)
3. **Performance**: Learn optimization techniques for real-time systems
4. **Integration**: Master Python ↔ C++ communication
5. **Testing**: Write comprehensive unit and integration tests
6. **Best Practices**: Follow SOLID principles, clean code, documentation

### Interview Preparation
- System design: Multi-component architecture, scaling considerations
- Coding: Design patterns, data structures, algorithms
- Behavioral: Design decisions, trade-offs, learning from mistakes

## File Structure

```
GameTrainer/
├── .agent/
│   ├── README.md              # AI assistant guidelines
│   └── workflows/             # (Future) Automated workflows
├── architecture.md            # High-level system design
├── design.md                  # Detailed implementation design
├── context.md                 # This file - current project state
├── tasks.md                   # Task tracking and thought process
├── src/
│   ├── python/
│   │   ├── main.py           # Entry point
│   │   ├── menu.py           # UI components
│   │   ├── orchestrator.py   # C++ facade
│   │   └── config.py         # Configuration management
│   └── cpp/
│       ├── cv_module.cpp     # Computer vision
│       ├── ai_engine.cpp     # AI decision making
│       └── input_module.cpp  # Input automation
├── tests/
│   ├── python/
│   └── cpp/
├── config/
│   └── game_config.json      # Game-specific settings
└── build/                     # C++ build artifacts
```

*Note: Actual structure to be confirmed after code review*

## Dependencies & Their Purposes

*To be populated after reviewing existing code and requirements*

### Why Each Dependency?

Example format:
- **OpenCV**: Computer vision operations (template matching, feature detection)
  - Alternative: Custom CV implementation (too much work)
  - Trade-off: Large library, but battle-tested and feature-rich

## Known Limitations

### Current Limitations
*To be documented*

### Future Enhancements
*To be documented as ideas emerge*

## Questions & Uncertainties

### Technical Questions
1. What C++/Python integration method is currently used?
2. What CV library (if any) is being used?
3. What's the current state of the AI implementation?
4. Are there existing tests?

### Design Questions
1. Should we support multiple games or focus on one?
2. What level of anti-detection is needed for input automation?
3. Should configuration be per-game or global?

### Learning Questions
1. Which design patterns should be prioritized for learning?
2. What interview topics are most relevant to this project?
3. How deep should we go into optimization vs readability?

## Communication Preferences

### Code Review Style
- **Prefer**: Detailed explanations with alternatives and trade-offs
- **Avoid**: "Here's the code" without context
- **Encourage**: Disagreement when better solutions exist

### Documentation Updates
- Update `tasks.md` every session
- Update `context.md` when project state changes significantly
- Update `design.md` when implementing new features
- Update `architecture.md` when adding major components

### Learning Focus
- Explain design patterns when used
- Relate to interview questions when relevant
- Discuss real-world production practices
- Compare alternatives and trade-offs

## Next Session Checklist

Before starting work in next session:
1. [ ] Review `tasks.md` for current priorities
2. [ ] Check `context.md` for recent changes
3. [ ] Review any open questions or blockers
4. [ ] Update task status as work progresses

After completing work:
1. [ ] Update `tasks.md` with completed items
2. [ ] Add new tasks discovered during work
3. [ ] Update `context.md` with significant changes
4. [ ] Document any new design decisions
5. [ ] Note any technical debt or future refactoring needs

---

**Remember**: This is a learning project. Prioritize understanding over speed, clarity over brevity, and education over efficiency.
