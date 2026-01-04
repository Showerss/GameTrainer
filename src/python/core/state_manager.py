"""
StateManager - Tracks game state across frames

Teacher Note: This class is the "memory" of the bot. While each frame gives us
a snapshot of the current moment, the StateManager remembers things across frames.

For Slice 1 (health detection), this is very simple - just store the current health.
Later, this will grow to track:
- Inventory contents
- Current location
- Relationships
- Farm state
- etc.

Design Philosophy:
    - Frame State: What we see RIGHT NOW (comes from vision)
    - Session State: What we've seen RECENTLY (in memory, lost on restart)
    - Persistent State: What we want to remember FOREVER (saved to disk)

For now, we only implement Frame State. Session and Persistent come later.
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class FrameState:
    """
    State extracted from a single frame.

    Teacher Note: This is what vision gives us each frame. It's the "current moment"
    snapshot. We use a dataclass for clean, typed access to the values.
    """
    # Health/Energy (0.0 to 1.0)
    health: float = 1.0
    energy: float = 1.0

    # When this state was captured
    timestamp: float = field(default_factory=time.time)

    # Raw confidence scores (how sure are we about each value?)
    # Teacher Note: Sometimes vision is uncertain - maybe the bar was partially
    # obscured or in a weird state. Confidence lets us handle uncertainty.
    confidence: Dict[str, float] = field(default_factory=lambda: {
        "health": 1.0,
        "energy": 1.0
    })


class StateManager:
    """
    Manages game state tracking across frames.

    Teacher Note: This is intentionally minimal for Slice 1. We just track
    the current state and provide a clean interface for the trainer loop.

    Usage:
        state = StateManager()

        # In the main loop:
        state.update_health(0.75)  # Set health to 75%
        print(f"Current health: {state.current.health}")

        # Check for low health:
        if state.is_health_critical():
            print("Health is critical!")
    """

    # Thresholds for "critical" levels
    HEALTH_CRITICAL = 0.30  # Below 30% = critical
    ENERGY_CRITICAL = 0.15  # Below 15% = critical

    def __init__(self):
        """
        Initialize the state manager.

        Teacher Note: We start with a default state (full health/energy).
        This will be overwritten as soon as the first frame is processed.
        """
        self._current = FrameState()
        self._previous: Optional[FrameState] = None

        # Statistics
        self._update_count = 0

    def update_health(self, value: float, confidence: float = 1.0) -> None:
        """
        Update the current health value.

        Args:
            value: Health percentage from 0.0 to 1.0
            confidence: How confident are we in this reading (0.0 to 1.0)

        Teacher Note: We clamp the value to valid range to prevent bugs
        from vision errors giving us values like -0.1 or 1.5.
        """
        # Clamp to valid range
        value = max(0.0, min(1.0, value))

        # Store previous state before updating
        if self._update_count > 0:
            self._previous = FrameState(
                health=self._current.health,
                energy=self._current.energy,
                timestamp=self._current.timestamp,
                confidence=self._current.confidence.copy()
            )

        # Update current state
        self._current.health = value
        self._current.confidence["health"] = confidence
        self._current.timestamp = time.time()
        self._update_count += 1

    def update_energy(self, value: float, confidence: float = 1.0) -> None:
        """
        Update the current energy value.

        Args:
            value: Energy percentage from 0.0 to 1.0
            confidence: How confident are we in this reading
        """
        value = max(0.0, min(1.0, value))
        self._current.energy = value
        self._current.confidence["energy"] = confidence
        self._current.timestamp = time.time()

    @property
    def current(self) -> FrameState:
        """Get the current frame state."""
        return self._current

    @property
    def previous(self) -> Optional[FrameState]:
        """Get the previous frame state (None if this is the first frame)."""
        return self._previous

    def is_health_critical(self) -> bool:
        """
        Check if health is at a critical level.

        Returns:
            True if health is below the critical threshold

        Teacher Note: This is a convenience method for the decision engine.
        Instead of checking `state.current.health < 0.3` everywhere,
        we encapsulate the threshold here.
        """
        return self._current.health < self.HEALTH_CRITICAL

    def is_energy_critical(self) -> bool:
        """Check if energy is at a critical level."""
        return self._current.energy < self.ENERGY_CRITICAL

    def health_changed(self) -> Optional[float]:
        """
        Check if health changed since last frame.

        Returns:
            The delta (positive = gained health, negative = lost health)
            None if this is the first frame

        Teacher Note: Detecting CHANGES is often more useful than absolute values.
        "I just took damage" is more actionable than "my health is 50%".
        """
        if self._previous is None:
            return None
        return self._current.health - self._previous.health

    def energy_changed(self) -> Optional[float]:
        """Check if energy changed since last frame."""
        if self._previous is None:
            return None
        return self._current.energy - self._previous.energy

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current state for logging/display.

        Returns:
            Dictionary with human-readable state info
        """
        return {
            "health": f"{self._current.health * 100:.0f}%",
            "energy": f"{self._current.energy * 100:.0f}%",
            "health_critical": self.is_health_critical(),
            "energy_critical": self.is_energy_critical(),
            "updates": self._update_count
        }
