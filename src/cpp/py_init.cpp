#include <Python.h>

static PyModuleDef ClibModule = {
    PyModuleDef_HEAD_INIT,
    "clib",
    "GameTrainer C Library",
    -1,
    NULL, NULL, NULL, NULL, NULL
};

extern "C" {
    PyMODINIT_FUNC PyInit_clib(void) {
        return PyModule_Create(&ClibModule);
    }
}
