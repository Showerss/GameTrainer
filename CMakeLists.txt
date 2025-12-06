cmake_minimum_required(VERSION 3.25)
project(GameTrainer)

cmake_minimum_required(VERSION 3.25)
project(GameTrainer)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)

include_directories(include)

# Create the shared library
add_library(libgametrainer SHARED
        src/cpp/input.cpp
        src/cpp/memory_manager.cpp
)

# Link necessary Windows libraries
target_link_libraries(libgametrainer PRIVATE user32 kernel32)