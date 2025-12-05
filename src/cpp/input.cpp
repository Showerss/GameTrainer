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