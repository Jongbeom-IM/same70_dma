cmake_minimum_required(VERSION 3.20)
project(SAME70CommTool)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(Threads REQUIRED)

# Platform-specific serial port libraries
if(WIN32)
    # Windows - no additional libraries needed for basic serial
    set(PLATFORM_LIBS "")
elseif(UNIX)
    # Linux/macOS
    set(PLATFORM_LIBS pthread)
endif()

# Source files
set(SOURCES
    src/main.cpp
    src/serial_comm.cpp
    src/protocol_handler.cpp
    src/data_logger.cpp
)

# Headers
set(HEADERS
    include/serial_comm.h
    include/protocol_handler.h
    include/data_logger.h
)

# Create executable
add_executable(${PROJECT_NAME} ${SOURCES} ${HEADERS})

# Include directories
target_include_directories(${PROJECT_NAME} PRIVATE include)

# Link libraries
target_link_libraries(${PROJECT_NAME} 
    Threads::Threads
    ${PLATFORM_LIBS}
)

# Compiler-specific flags
if(MSVC)
    target_compile_options(${PROJECT_NAME} PRIVATE /W4)
else()
    target_compile_options(${PROJECT_NAME} PRIVATE -Wall -Wextra -pedantic)
endif()