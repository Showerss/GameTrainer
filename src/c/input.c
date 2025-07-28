#include "input.h"
#include <stdlib.h>
#include <time.h>// Wraps a relative mouse move.
void SendMouseMove(int dx, int dy) {
    INPUT inp = { .type = INPUT_MOUSE };
    inp.mi.dx      = dx;
    inp.mi.dy      = dy;
    inp.mi.dwFlags = MOUSEEVENTF_MOVE;
    SendInput(1, &inp, sizeof(inp));
}

// Breaks a long move into small, slightly randomized steps.
void JitteredMouseMove(int targetX, int targetY) {
    // Seed once in your main(): srand((unsigned)time(NULL));
    int steps = 10 + rand() % 5;
    for (int i = 1; i <= steps; ++i) {
        float frac = (float)i / steps;
        int x = (int)(frac * targetX) + (rand() % 3 - 1);
        int y = (int)(frac * targetY) + (rand() % 3 - 1);
        SendMouseMove(x, y);
        // ~75ms ±15ms pause
        Sleep(75 + (rand() % 30 - 15));
    }
}

// Simple key down + key up.
void SendKey(WORD vkCode) {
    INPUT inputs[2] = {0};
    // key down
    inputs[0].type        = INPUT_KEYBOARD;
    inputs[0].ki.wVk      = vkCode;
    // key up
    inputs[1].type        = INPUT_KEYBOARD;
    inputs[1].ki.wVk      = vkCode;
    inputs[1].ki.dwFlags  = KEYEVENTF_KEYUP;
    SendInput(2, inputs, sizeof(inputs[0]));
}