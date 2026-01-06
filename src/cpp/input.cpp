#include "input.h"
#include <random>
#include <thread>
#include <chrono>

namespace {
    std::mt19937& GetRNG() {
        static thread_local std::mt19937 generator(std::random_device{}());
        return generator;
    }
}

// Wraps a relative mouse move.
void SendMouseMove(int dx, int dy) {
    INPUT inp = {0};
    inp.type = INPUT_MOUSE;
    inp.mi.dx      = dx;
    inp.mi.dy      = dy;
    inp.mi.dwFlags = MOUSEEVENTF_MOVE;
    SendInput(1, &inp, sizeof(inp));
}

// Breaks a long move into small, slightly randomized steps.
void JitteredMouseMove(int targetX, int targetY) {
    auto& rng = GetRNG();
    std::uniform_int_distribution<int> step_dist(10, 15);
    std::uniform_int_distribution<int> jitter_dist(-1, 1);
    std::uniform_int_distribution<int> sleep_dist(60, 90);

    int steps = step_dist(rng);
    for (int i = 1; i <= steps; ++i) {
        float frac = (float)i / steps;
        int x = (int)(frac * targetX) + jitter_dist(rng);
        int y = (int)(frac * targetY) + jitter_dist(rng);
        SendMouseMove(x, y);
        
        std::this_thread::sleep_for(std::chrono::milliseconds(sleep_dist(rng)));
    }
}

// Sends a left mouse button click (down + up).
// Note: Added delay between down/up to help games register the click.
void SendMouseClick() {
    INPUT inputs[2] = {0};
    // Left button down
    inputs[0].type = INPUT_MOUSE;
    inputs[0].mi.dwFlags = MOUSEEVENTF_LEFTDOWN;
    inputs[0].mi.dwExtraInfo = 0;
    // Left button up
    inputs[1].type = INPUT_MOUSE;
    inputs[1].mi.dwFlags = MOUSEEVENTF_LEFTUP;
    inputs[1].mi.dwExtraInfo = 0;
    
    // Send down
    SendInput(1, &inputs[0], sizeof(INPUT));
    // Small delay
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    // Send up
    SendInput(1, &inputs[1], sizeof(INPUT));
}

// Sends a right mouse button click (down + up).
// Note: Added delay between down/up to help games register the click.
void SendMouseRightClick() {
    INPUT inputs[2] = {0};
    // Right button down
    inputs[0].type = INPUT_MOUSE;
    inputs[0].mi.dwFlags = MOUSEEVENTF_RIGHTDOWN;
    inputs[0].mi.dwExtraInfo = 0;
    // Right button up
    inputs[1].type = INPUT_MOUSE;
    inputs[1].mi.dwFlags = MOUSEEVENTF_RIGHTUP;
    inputs[1].mi.dwExtraInfo = 0;
    
    // Send down
    SendInput(1, &inputs[0], sizeof(INPUT));
    // Small delay
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    // Send up
    SendInput(1, &inputs[1], sizeof(INPUT));
}

// Simple key down + key up.
// Teacher Note: Games using DirectInput (like Stardew Valley / MonoGame) read
// HARDWARE SCAN CODES, not virtual key codes. Virtual keys work for regular apps
// (Notepad, browsers) but games bypass the Windows message queue and read directly
// from the keyboard driver. We must use KEYEVENTF_SCANCODE to simulate hardware input.
void SendKey(WORD vkCode) {
    INPUT inputs[2] = {0};

    // Convert virtual key to hardware scan code
    // Teacher Note: MapVirtualKey translates between VK codes and scan codes.
    // MAPVK_VK_TO_VSC gives us the scan code that the physical key would generate.
    UINT scanCode = MapVirtualKey(vkCode, MAPVK_VK_TO_VSC);

    // Key down - using SCAN CODE (critical for games!)
    inputs[0].type        = INPUT_KEYBOARD;
    inputs[0].ki.wVk      = 0;  // Must be 0 when using scan codes
    inputs[0].ki.wScan    = scanCode;
    inputs[0].ki.dwFlags  = KEYEVENTF_SCANCODE;  // This flag tells Windows to use wScan
    inputs[0].ki.dwExtraInfo = 0;

    // Key up - also using scan code
    inputs[1].type        = INPUT_KEYBOARD;
    inputs[1].ki.wVk      = 0;
    inputs[1].ki.wScan    = scanCode;
    inputs[1].ki.dwFlags  = KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP;
    inputs[1].ki.dwExtraInfo = 0;

    // Send key down
    SendInput(1, &inputs[0], sizeof(INPUT));

    // Small delay - some games need this to register the key press
    std::this_thread::sleep_for(std::chrono::milliseconds(10));

    // Send key up
    SendInput(1, &inputs[1], sizeof(INPUT));
}

// Alternative method: Send key directly to window using PostMessage.
// This can bypass some games' input detection mechanisms.
int SendKeyToWindow(HWND hwnd, WORD vkCode) {
    if (hwnd == NULL || !IsWindow(hwnd)) {
        return 0;  // Invalid window handle
    }
    
    // Get scan code for the virtual key
    UINT scanCode = MapVirtualKey(vkCode, MAPVK_VK_TO_VSC);
    
    // Send WM_KEYDOWN
    LPARAM lParamDown = (scanCode << 16) | (1 << 25);  // Scan code + extended key flag
    PostMessage(hwnd, WM_KEYDOWN, vkCode, lParamDown);
    
    // Small delay
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    
    // Send WM_KEYUP
    LPARAM lParamUp = (scanCode << 16) | (1 << 25) | (1 << 30) | (1 << 31);  // + key was down + transition
    PostMessage(hwnd, WM_KEYUP, vkCode, lParamUp);
    
    return 1;  // Success
}