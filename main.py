from src.python.gui.main_window import GameTrainerGUI
from src.python.core.trainer import GameTrainer  # This would be your wrapper for C functions
import tkinter as tk

def main():
    # Initialize the trainer (C functions wrapper)
    trainer = GameTrainer()

    # Initialize GUI with trainer instance
    root = tk.Tk()
    app = GameTrainerGUI(root)
    app.run()

if __name__ == "__main__":
    main()
