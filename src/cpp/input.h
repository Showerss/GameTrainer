#ifndef INPUT_H
#define INPUT_H

#include <Windows.h>

#ifdef _WIN32
  #define GT_EXPORT __declspec(dllexport)
#else
  #define GT_EXPORT
#endif

#ifdef __cplusplus
extern "C" {
#endif

// Moves the mouse by (dx, dy) in one shot.
GT_EXPORT void SendMouseMove(int dx, int dy);

// Moves the mouse to (targetX, targetY) in small jittered steps.
GT_EXPORT void JitteredMouseMove(int x, int y);

// Sends a single key press-and-release of virtual-key vkCode.
GT_EXPORT void SendKey(WORD vkCode);

#ifdef __cplusplus
}
#endif

#endif // INPUT_H