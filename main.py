from src.python.gui.main_window import GameTrainerGUI
from src.python.core.io.process_client import ProcessClient
import tkinter as tk

def main():
    # Initialize the trainer (C functions wrapper)
    trainer = GameTrainer()

    # Initialize GUI with trainer instance
    root = tk.Tk()
    app = GameTrainerGUI(root, trainer)
    app.run()

if __name__ == "__main__":
    main()
