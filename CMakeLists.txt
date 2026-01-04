# GameTrainer CMake Configuration
#
# Teacher Note: CMake is a build system generator. It creates the actual
# build files (like Makefiles or Visual Studio projects) from this config.
# We use it to compile our C++ input simulation code.

cmake_minimum_required(VERSION 3.15)
project(GameTrainer VERSION 2.0)

# Use C++17 standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Export all symbols on Windows (makes DLL creation easier)
set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)

# Include directories
include_directories(include)

# ─────────────────────────────────────────────────────────────────────────────
# Input Simulator Library
# Teacher Note: This creates a shared library (.dll on Windows) containing
# our input simulation code. It wraps Windows SendInput API for keyboard
# and mouse control.
# ─────────────────────────────────────────────────────────────────────────────
add_library(gametrainer_input SHARED
    src/cpp/input.cpp
)

# Link Windows libraries needed for input simulation
# - user32: Contains SendInput, keybd_event, mouse_event
# - kernel32: Basic Windows functions
target_link_libraries(gametrainer_input PRIVATE
    user32
    kernel32
)

# Set output name without 'lib' prefix on Windows
set_target_properties(gametrainer_input PROPERTIES
    PREFIX ""
    OUTPUT_NAME "gametrainer_input"
)

# ─────────────────────────────────────────────────────────────────────────────
# Optional: Build Python extension directly with CMake
# Teacher Note: Usually we use setup.py to build the Python extension,
# but this target is here for standalone testing of the C++ code.
# ─────────────────────────────────────────────────────────────────────────────
# find_package(Python3 COMPONENTS Development)
# if(Python3_FOUND)
#     add_library(clib SHARED
#         src/cpp/input.cpp
#         src/cpp/py_init.cpp
#     )
#     target_link_libraries(clib PRIVATE Python3::Python user32 kernel32)
#     set_target_properties(clib PROPERTIES
#         PREFIX ""
#         SUFFIX ".pyd"
#     )
# endif()
