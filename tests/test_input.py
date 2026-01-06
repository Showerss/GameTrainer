"""
Quick test script to verify input is working.
Run this with Stardew Valley open.
"""

import time
from src.gametrainer.input import InputController

print("=" * 60)
print("INPUT TEST SCRIPT")
print("=" * 60)
print("\nThis will test if keyboard and mouse inputs are working.")
print("\nIMPORTANT: Make sure Stardew Valley is OPEN (doesn't need to be focused yet)")
print("\nYou'll have time to switch to the game window before testing starts.")
print("\n" + "=" * 60)

# Give user time to read
time.sleep(2)

print("\nChoose timing:")
print("  1. Automatic countdown (10 seconds)")
print("  2. Press Enter when ready (recommended)")
choice = input("\nEnter choice (1 or 2, default=2): ").strip()

if choice == "1":
    print("\nStarting countdown...")
    print("Switch to Stardew Valley window NOW!")
    for i in range(10, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
else:
    print("\nSwitch to Stardew Valley window and make sure it's FOCUSED.")
    input("Press Enter when you're ready to start testing...")
    print("\nStarting in 2 seconds...")
    time.sleep(2)

print("\n" + "=" * 60)
print("TESTING NOW - Watch your game window!")
print("=" * 60 + "\n")

input_ctrl = InputController()

# Test each input with longer delays so user can see what's happening
print("1. Testing W key (should move UP)...")
input_ctrl.move_up()
time.sleep(1)

print("2. Testing S key (should move DOWN)...")
input_ctrl.move_down()
time.sleep(1)

print("3. Testing A key (should move LEFT)...")
input_ctrl.move_left()
time.sleep(1)

print("4. Testing D key (should move RIGHT)...")
input_ctrl.move_right()
time.sleep(1)

print("\n5. Testing LEFT mouse click...")
input_ctrl.mouse_click()
time.sleep(1)

print("6. Testing RIGHT mouse click...")
input_ctrl.mouse_right_click()
time.sleep(1)

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
print("\nDid you see:")
print("  - Character movement (W/A/S/D keys)?")
print("  - Mouse clicks in the game?")
print("\nIf you saw movement/clicks: Input is working!")
print("If you saw nothing: There may be an issue with:")
print("  - Game window not receiving focus")
print("  - C++ extension not working")
print("  - Game blocking simulated inputs")
print("  - Need to run as administrator")
print("\n" + "=" * 60)
