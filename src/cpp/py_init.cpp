#include <Python.h>
#include "input.h"

// Python wrapper for SendKey
static PyObject* method_send_key(PyObject* self, PyObject* args) {
    int vkCode;
    // Parse integer argument
    if (!PyArg_ParseTuple(args, "i", &vkCode)) {
        return NULL;
    }
    SendKey((WORD)vkCode);
    Py_RETURN_NONE;
}

// Python wrapper for SendMouseMove
static PyObject* method_send_mouse_move(PyObject* self, PyObject* args) {
    int dx, dy;
    if (!PyArg_ParseTuple(args, "ii", &dx, &dy)) {
        return NULL;
    }
    SendMouseMove(dx, dy);
    Py_RETURN_NONE;
}

// Python wrapper for JitteredMouseMove
static PyObject* method_jitter_move(PyObject* self, PyObject* args) {
    int x, y;
    if (!PyArg_ParseTuple(args, "ii", &x, &y)) {
        return NULL;
    }
    JitteredMouseMove(x, y);
    Py_RETURN_NONE;
}

// Method definition table
static PyMethodDef ClibMethods[] = {
    {"send_key", method_send_key, METH_VARARGS, "Send a key press (VK code)."},
    {"send_mouse_move", method_send_mouse_move, METH_VARARGS, "Move mouse relative (dx, dy)."},
    {"jitter_move", method_jitter_move, METH_VARARGS, "Move mouse relative with jitter (dx, dy)."},
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