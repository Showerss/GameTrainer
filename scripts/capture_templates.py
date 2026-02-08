import cv2
import mss
import numpy as np
import os
import time

def capture_template():
    print("="*60)
    print("TEMPLATE CAPTURE TOOL")
    print("="*60)
    print("1. Open Stardew Valley")
    print("2. Make sure the UI element you want (e.g., Energy Icon) is visible")
    print("3. Switch back here and press ENTER to capture screen")
    
    input("Press ENTER to capture...")
    
    with mss.mss() as sct:
        # Capture full screen (monitor 1)
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
    print("\n[INSTRUCTIONS]")
    print("- Drag mouse to draw a box around the element")
    print("- Press SPACE or ENTER to confirm selection")
    print("- Press c to cancel")
    
    # Select ROI
    r = cv2.selectROI("Select Template", img, fromCenter=False, showCrosshair=True)
    cv2.destroyAllWindows()
    
    # r is (x, y, w, h)
    if r[2] == 0 or r[3] == 0:
        print("Selection cancelled.")
        return

    # Crop
    imCrop = img[int(r[1]):int(r[1]+r[3]), int(r[0]):int(r[0]+r[2])]
    
    # Save
    name = input("\nEnter filename (e.g., 'energy_icon'): ")
    if not name.endswith(".png"):
        name += ".png"
        
    save_path = os.path.join("src", "gametrainer", "templates", name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    cv2.imwrite(save_path, imCrop)
    print(f"\nSaved to: {save_path}")
    print("Done!")

if __name__ == "__main__":
    capture_template()
