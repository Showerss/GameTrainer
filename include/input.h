#ifndef INPUT_H
#define INPUT_H

#include <Windows.h>

// Moves the mouse by (dx, dy) in one shot.
void SendMouseMove(int dx, int dy);

// Moves the mouse to (targetX, targetY) in small jittered steps.
void JitteredMouseMove(int targetX, int targetY);

// Sends a single key press-and-release of virtual-key vkCode.
void SendKey(WORD vkCode);

#endif // INPUT_H
