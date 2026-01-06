"""
GameTrainer - Local RL Edition

This is the entry point for the GameTrainer CLI.
Use this to launch training or inference sessions.
"""

import sys
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description="GameTrainer CLI")
    parser.add_argument("mode", choices=["train", "play"], help="Mode: 'train' the agent or let it 'play'")
    
    args = parser.parse_args()
    
    if args.mode == "train":
        print("Launching training session...")
        subprocess.run([sys.executable, "train.py"])
    elif args.mode == "play":
        print("Inference mode not implemented yet.")
        print("Run 'python train.py' to train your agent first!")

if __name__ == "__main__":
    main()