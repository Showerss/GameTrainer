# 2. trainer.py is a high level loop that polls information coming from memory_controller.py every 0.1s.
# It compares the game state (energy, health, etc.) to the thresholds set in the GUI.
# If thresholds are met, it triggers actions.

import ctypes
from pathlib import Path
import time
import threading
from src.python.core.memory_controller import MemoryController
from src.python.core.logger import Logger
# We will need this later for the AI vision part!
from src.python.core.pixel_detector import PixelDetector 

class GameTrainer:
    """
    The main brain of the bot.
    It runs in a separate thread loops forever (until stopped) checking 
    if the game character needs help (like healing or eating).
    """
    def __init__(self):
        self.memory = MemoryController()
        self.logger = Logger()
        self.detector = PixelDetector() # Our "eyes" for the game
        self.running = False
        self.paused = False
        self.thread = None

    def start(self):
        """Starts the background monitoring loop."""
        if self.running:
            return
        
        self.logger.log("Trainer starting...")
        # Try to hook into the game process
        if not self.memory.attach():
            self.logger.log("Failed to attach to process. Is the game running?")
            self.logger.log("Teacher Tip: Make sure the game is open before starting!")
            return

        self.running = True
        self.paused = False
        # thread logic: run self._loop in the background so the GUI doesn't freeze
        self.thread = threading.Thread(target=self._loop)
        self.thread.daemon = True # Dies if the main program closes
        self.thread.start()
        self.logger.log("Trainer started.")

    def stop(self):
        """Stops the monitoring loop."""
        self.running = False
        if self.thread:
            self.thread.join() # Wait for the loop to actually finish
        self.memory.detach()
        self.logger.log("Trainer stopped.")

    def pause(self):
        """Temporarily pauses the logic without stopping the thread."""
        self.paused = not self.paused
        state = "paused" if self.paused else "resumed"
        self.logger.log(f"Trainer {state}.")

    def _loop(self):
        """
        The heartbeat of the bot. Runs 10 times a second.
        """
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue

            # 1. READ Game State (Memory or Vision)
            energy = self.memory.read_energy()
            
            # 2. DECIDE what to do
            # Example: If energy is low, we might need to eat.
            # print(f"Current Energy: {energy}")

            # 3. ACT (Simulate keypresses - Coming Soon!)
            # if energy < 10:
            #     input_simulator.press_key('F1')
            
            time.sleep(0.1) # 10 Hz (Run 10 times per second)