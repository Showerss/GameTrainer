from src.python.gui import GameTrainerGUI
from src.python.core.trainer import GameTrainer  # This would be your wrapper for C functions

def main():
    # Initialize the trainer (C functions wrapper)
    trainer = GameTrainer()

    # Initialize GUI with trainer instance
    app = GameTrainerGUI(trainer)
    app.run()

if __name__ == "__main__":
    main()