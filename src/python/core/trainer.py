"""
GameTrainer - Main Orchestration Module

Teacher Note: This is the "brain" of the bot. It coordinates all the other
components in a continuous loop:

    1. CAPTURE  - Take a screenshot of the game
    2. EXTRACT  - Convert pixels into game state (health, stamina, etc.)
    3. DECIDE   - Look up which rule matches the current state
    4. ACT      - Execute the action (press keys, move mouse)
    5. VERIFY   - Check if the action worked as expected

The loop runs at 10 FPS (every 100ms), which is plenty fast for most games.
Remember: We're watching the screen like a human would - no memory reading!
"""

import time
import threading
from typing import Optional

from src.python.core.logger import Logger
from src.python.core.pixel_detector import PixelDetector
from src.python.core.screen_capture import ScreenCapture
from src.python.core.config_loader import ConfigLoader
from src.python.core.state_manager import StateManager
from src.python.core.vision import HealthDetector


class GameTrainer:
    """
    The main orchestrator for GameTrainer.

    Teacher Note: This class follows the "Coordinator" or "Mediator" pattern.
    It doesn't do the actual work - it just tells other components what to
    do and when. This keeps each component simple and testable.

    Lifecycle:
        1. __init__() - Create all components
        2. start()    - Begin the main loop in a background thread
        3. _loop()    - Runs continuously until stop() is called
        4. stop()     - Clean shutdown

    Example:
        trainer = GameTrainer()
        trainer.start()
        # ... bot is now running ...
        trainer.stop()
    """

    # Configuration constants
    TARGET_FPS = 10  # How many times per second we process a frame
    FRAME_TIME = 1.0 / TARGET_FPS  # Time budget per frame (100ms)

    def __init__(self, profile_path: str = "profiles/stardew_valley"):
        """
        Initialize all components.

        Args:
            profile_path: Path to the game profile folder containing regions.yaml, etc.

        Teacher Note: We create all our "workers" here but don't start
        anything yet. This follows the principle of "construct, then start"
        which makes the code easier to test and debug.
        """
        # Core components
        self.logger = Logger()
        self.detector = PixelDetector()  # Our "eyes" - analyzes what we see
        self.screen_capture = ScreenCapture()  # Grabs screenshots

        # Configuration
        self.config = ConfigLoader(profile_path)
        self.logger.log(f"Loaded profile: {self.config.profile_name}")

        # State management (Slice 1: just health/energy tracking)
        self.state = StateManager()

        # Vision components (Slice 1: health/energy detection)
        # Teacher Note: We initialize detectors with region configs from the profile.
        # If a region isn't defined, we use fallback defaults.
        energy_region = self.config.get_region("energy_bar") or {
            "x": 1260, "y": 595, "width": 25, "height": 175
        }
        self.energy_detector = HealthDetector(energy_region)

        # TODO: These will be added as we implement the full architecture
        # self.knowledge_base = KnowledgeBase()
        # self.decision_engine = DecisionEngine()
        # self.input_simulator = InputSimulator()
        # self.outcome_verifier = OutcomeVerifier()

        # Runtime state
        self.running = False
        self.paused = False
        self._thread: Optional[threading.Thread] = None

        # Statistics (useful for debugging)
        self._frame_count = 0
        self._start_time = 0.0

        # Debug: log every N frames (to avoid spam)
        self._log_interval = 30  # Log state every 30 frames (3 seconds at 10 FPS)

    def start(self) -> bool:
        """
        Start the trainer loop in a background thread.

        Returns:
            True if started successfully, False otherwise

        Teacher Note: We use a background thread so the GUI stays responsive.
        If we ran the loop on the main thread, the window would freeze.
        """
        if self.running:
            self.logger.log("Trainer is already running.")
            return False

        self.logger.log("Trainer starting...")

        # TODO: Initialize screen capture region
        # if not self.screen_capture.set_region_from_window("Game Window"):
        #     self.logger.log("Could not find game window!")
        #     return False

        # TODO: Load knowledge base
        # if not self.knowledge_base.load("knowledge/game_name/knowledge_base.json"):
        #     self.logger.log("Could not load knowledge base!")
        #     return False

        self.running = True
        self.paused = False
        self._frame_count = 0
        self._start_time = time.time()

        # Start the loop in a background thread
        # daemon=True means the thread dies when the main program exits
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

        self.logger.log("Trainer started successfully.")
        self.logger.log("Teacher Tip: The bot is now watching the screen at 10 FPS.")
        return True

    def stop(self) -> None:
        """
        Stop the trainer loop and clean up resources.

        Teacher Note: We set running=False and then wait for the thread to
        finish (join). This ensures a clean shutdown with no orphaned threads.
        """
        if not self.running:
            self.logger.log("Trainer is not running.")
            return

        self.logger.log("Trainer stopping...")
        self.running = False

        # Wait for the loop thread to finish
        if self._thread is not None:
            self._thread.join(timeout=2.0)  # Wait up to 2 seconds
            self._thread = None

        # Log statistics
        elapsed = time.time() - self._start_time
        if elapsed > 0:
            actual_fps = self._frame_count / elapsed
            self.logger.log(f"Ran for {elapsed:.1f}s, {self._frame_count} frames ({actual_fps:.1f} FPS)")

        self.logger.log("Trainer stopped.")

    def pause(self) -> None:
        """
        Toggle pause state.

        Teacher Note: When paused, the loop keeps running but skips all
        processing. This is useful when the user needs to interact with
        the game manually.
        """
        self.paused = not self.paused
        state = "paused" if self.paused else "resumed"
        self.logger.log(f"Trainer {state}.")

    def _loop(self) -> None:
        """
        The main processing loop. Runs at TARGET_FPS.

        Teacher Note: This is where the magic happens! Each iteration:
        1. Captures the screen
        2. Extracts game state from the image
        3. Decides what action to take
        4. Executes the action
        5. Verifies the outcome

        We use time.sleep() to maintain a consistent frame rate. This is
        important because we don't want to waste CPU cycles or make the
        bot behave erratically.
        """
        self.logger.log("Main loop started.")

        while self.running:
            frame_start = time.time()

            # Skip processing if paused
            if self.paused:
                time.sleep(self.FRAME_TIME)
                continue

            # ─────────────────────────────────────────────────────────
            # PHASE 1: CAPTURE
            # Grab a screenshot of the game window
            # ─────────────────────────────────────────────────────────
            frame = self.screen_capture.grab()
            if frame is None:
                # No frame captured - maybe region not set or error occurred
                time.sleep(self.FRAME_TIME)
                continue

            # ─────────────────────────────────────────────────────────
            # PHASE 2: EXTRACT
            # Convert the image into meaningful game state
            # ─────────────────────────────────────────────────────────
            # TODO: game_state = self.state_extractor.extract_state(frame)

            # ─────────────────────────────────────────────────────────
            # PHASE 3: VERIFY PREVIOUS ACTION
            # Check if the last action worked as expected
            # ─────────────────────────────────────────────────────────
            # TODO: self.outcome_verifier.verify(game_state, frame)

            # ─────────────────────────────────────────────────────────
            # PHASE 4: DECIDE
            # Look up which rule matches the current state
            # ─────────────────────────────────────────────────────────
            # TODO: decision = self.decision_engine.decide(game_state)

            # ─────────────────────────────────────────────────────────
            # PHASE 5: ACT
            # Execute the action (if any)
            # ─────────────────────────────────────────────────────────
            # TODO: if decision:
            # TODO:     self.outcome_verifier.expect(decision.expected_outcome, game_state)
            # TODO:     self.input_simulator.execute_action(decision.action)

            # Update statistics
            self._frame_count += 1

            # Sleep to maintain target FPS
            frame_elapsed = time.time() - frame_start
            sleep_time = self.FRAME_TIME - frame_elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
            elif frame_elapsed > self.FRAME_TIME * 1.5:
                # Log warning if we're falling behind
                self.logger.log(f"Warning: Frame took {frame_elapsed*1000:.1f}ms (budget: {self.FRAME_TIME*1000:.1f}ms)")

        self.logger.log("Main loop ended.")

    @property
    def is_running(self) -> bool:
        """Check if the trainer is currently running."""
        return self.running

    @property
    def is_paused(self) -> bool:
        """Check if the trainer is currently paused."""
        return self.paused

    @property
    def stats(self) -> dict:
        """
        Get current statistics.

        Returns:
            Dictionary with frame_count, elapsed_time, fps
        """
        elapsed = time.time() - self._start_time if self.running else 0
        return {
            "frame_count": self._frame_count,
            "elapsed_time": elapsed,
            "fps": self._frame_count / elapsed if elapsed > 0 else 0
        }
