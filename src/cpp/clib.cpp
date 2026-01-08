#include <Python.h>
#include <Windows.h>
#include <random>
#include <thread>
#include <chrono>

// ============================================================================
// PART 1: NATIVE INPUT IMPLEMENTATION
// ============================================================================

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
// HARDWARE SCAN CODES, not virtual key codes. We use MapVirtualKey to find them.
void SendKey(WORD vkCode) {
    INPUT inputs[2] = {0};

    // Convert virtual key to hardware scan code
    UINT scanCode = MapVirtualKey(vkCode, MAPVK_VK_TO_VSC);

    // Key down - using SCAN CODE (critical for games!)
    inputs[0].type        = INPUT_KEYBOARD;
    inputs[0].ki.wVk      = 0;  // Must be 0 when using scan codes
    inputs[0].ki.wScan    = scanCode;
    inputs[0].ki.dwFlags  = KEYEVENTF_SCANCODE;
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


// ============================================================================
// PART 2: PYTHON BINDINGS (C API)
// ============================================================================

// Python wrapper for SendKey
static PyObject* method_send_key(PyObject* self, PyObject* args) {
    int vkCode;
    if (!PyArg_ParseTuple(args, "i", &vkCode)) return NULL;
    SendKey((WORD)vkCode);
    Py_RETURN_NONE;
}

// Python wrapper for SendMouseMove
static PyObject* method_send_mouse_move(PyObject* self, PyObject* args) {
    int dx, dy;
    if (!PyArg_ParseTuple(args, "ii", &dx, &dy)) return NULL;
    SendMouseMove(dx, dy);
    Py_RETURN_NONE;
}

// Python wrapper for JitteredMouseMove
static PyObject* method_jitter_move(PyObject* self, PyObject* args) {
    int x, y;
    if (!PyArg_ParseTuple(args, "ii", &x, &y)) return NULL;
    JitteredMouseMove(x, y);
    Py_RETURN_NONE;
}

// Python wrapper for SendMouseClick
static PyObject* method_send_mouse_click(PyObject* self, PyObject* args) {
    if (!PyArg_ParseTuple(args, "")) return NULL;
    SendMouseClick();
    Py_RETURN_NONE;
}

// Python wrapper for SendMouseRightClick
static PyObject* method_send_mouse_right_click(PyObject* self, PyObject* args) {
    if (!PyArg_ParseTuple(args, "")) return NULL;
    SendMouseRightClick();
    Py_RETURN_NONE;
}

// Method definition table
static PyMethodDef ClibMethods[] = {
    {"send_key", method_send_key, METH_VARARGS, "Send a key press (VK code)."},
    {"send_mouse_move", method_send_mouse_move, METH_VARARGS, "Move mouse relative (dx, dy)."},
    {"jitter_move", method_jitter_move, METH_VARARGS, "Move mouse relative with jitter (dx, dy)."},
    {"send_mouse_click", method_send_mouse_click, METH_VARARGS, "Send a left mouse button click."},
    {"send_mouse_right_click", method_send_mouse_right_click, METH_VARARGS, "Send a right mouse button click."},
    {NULL, NULL, 0, NULL} // Sentinel
};

// Module definition
static PyModuleDef ClibModule = {
    PyModuleDef_HEAD_INIT,
    "clib",
    "GameTrainer C Library",
    -1,
    ClibMethods
};

// Module initialization function
extern "C" {
    PyMODINIT_FUNC PyInit_clib(void) {
        return PyModule_Create(&ClibModule);
    }
}
