from src.python.gui.main_window import GameTrainerGUI
from src.python.core.trainer import GameTrainer  # <--- Teacher Note: We need to import the class to use it!
from src.python.core.io.process_client import ProcessClient
import tkinter as tk

# Welcome to the Main Entry Point!
# This file is like the front door of our application. 
# It sets up the backend (GameTrainer) and the frontend (GameTrainerGUI) and connects them.

def main():
    # 1. Initialize the trainer
    # This is the "brain" of our bot that will talk to the C++ code.
    trainer = GameTrainer()

    # 2. Initialize GUI with trainer instance
    # We pass the 'trainer' to the GUI so the buttons (Start/Stop) can control it.
    root = tk.Tk()
    app = GameTrainerGUI(root, trainer)
    
    # 3. Start the application loop
    # This keeps the window open until you click 'X'.
    app.run()

if __name__ == "__main__":
    main()
