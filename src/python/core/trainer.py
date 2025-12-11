# 2. trainer.py is a high level loop that polls information coming from memory_controller.py every 0.5s and compares the energy, health, etc to the 
# thresholds set in the trainer GUI.  If the thresholds are met, the trainer will use the input simulator to perform the actions needed to 
# reach the thresholds, it will also load a C .dll that use windows actions to perform the actions needed to reach the thresholds


import ctypes
from pathlib import Path
import time
import threading
from src.python.core.memory_controller import MemoryController
from src.python.core.logger import Logger

class GameTrainer:
    def __init__(self):
        self.memory = MemoryController()
        self.logger = Logger()
        self.running = False
        self.paused = False
        self.thread = None

    def start(self):
        if self.running:
            return
        
        self.logger.log("Trainer starting...")
        if not self.memory.attach():
            self.logger.log("Failed to attach to process. Is the game running?")
            return

        self.running = True
        self.paused = False
        self.thread = threading.Thread(target=self._loop)
        self.thread.daemon = True
        self.thread.start()
        self.logger.log("Trainer started.")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        self.memory.detach()
        self.logger.log("Trainer stopped.")

    def pause(self):
        self.paused = not self.paused
        state = "paused" if self.paused else "resumed"
        self.logger.log(f"Trainer {state}.")

    def _loop(self):
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue

            # Main Logic Loop
            energy = self.memory.read_energy()
            if energy is not None:
                # self.logger.log(f"Energy: {energy}")
                pass
            
            # TODO: Add behavior logic here (e.g., if energy < 10, eat food)
            
            time.sleep(0.1) # 10 Hz