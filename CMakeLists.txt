cmake_minimum_required(VERSION 3.25)
project(GameTrainer)

set(CMAKE_C_STANDARD 23)
set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)

include_directories(include)

# First create your shared library
add_library(GameTrainerLib SHARED
        src/c/input.c
#        src/c/memory_ops.c  # Adjust path as needed
        sec/c/memory.c

)

# Add an executable target
add_executable(GameTrainer
        src/c/memory_manager.c
        src/c/memory_manager.h
        src/c/input_simulator.c
        src/c/input_simulator.h
        src/c/process_handler.c
        src/c/process_handler.h
        src/c/interface/interface.c
        src/c/interface/interface.h  # Make sure this file exists
)

# Link the executable with the library
target_link_libraries(GameTrainer PRIVATE GameTrainerLib)