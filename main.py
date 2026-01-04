"""
GameTrainer - Main Entry Point

Teacher Note: This file is like the "front door" of our application.
When you run `python main.py`, execution starts here. This file:

    1. Creates the GameTrainer (the backend "brain")
    2. Creates the GUI (the frontend window)
    3. Connects them together
    4. Starts the application loop

The separation of trainer and GUI follows the "Model-View" pattern:
    - Model (GameTrainer): Does the actual work
    - View (GameTrainerGUI): Shows information and accepts user input

This separation means we could swap out the GUI for a different one
(or even run headless) without changing the trainer logic.
"""

from src.python.gui.main_window import GameTrainerGUI
from src.python.core.trainer import GameTrainer
import tkinter as tk


def main():
    """
    Application entry point.

    Teacher Note: This function sets up everything and starts the app.
    The order matters:
        1. Create trainer first (it's independent)
        2. Create GUI with trainer reference (GUI depends on trainer)
        3. Start the GUI event loop (blocks until window closes)
    """
    # 1. Initialize the trainer
    # This is the "brain" that will watch the screen and make decisions.
    trainer = GameTrainer()

    # 2. Initialize GUI with trainer instance
    # We pass the trainer to the GUI so buttons can control it.
    root = tk.Tk()
    app = GameTrainerGUI(root, trainer)

    # 3. Start the application loop
    # This keeps the window open and responsive until you close it.
    # Teacher Note: mainloop() blocks here until the window is closed.
    app.run()


if __name__ == "__main__":
    main()
