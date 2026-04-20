cmake_minimum_required(VERSION 3.20)
project(dm73parser VERSION 0.1.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Suppress MSVC warnings about C99-style stdio functions (fopen, snprintf, etc.)
if(MSVC)
    add_compile_definitions(_CRT_SECURE_NO_WARNINGS)
endif()

# ---------------------------------------------------------------------------
# Vendored wolfcamql / Q3A sources (GPL-2.0, original headers preserved)
# Source tree: engine/engines/_canonical/code/qcommon/
# Copy or symlink before building — see README.md in this directory.
# ---------------------------------------------------------------------------
set(VENDOR_SRCS
    vendor/msg.c
    vendor/huffman.c
    vendor/common.c
)

# ---------------------------------------------------------------------------
# Static library: dm73
# ---------------------------------------------------------------------------
add_library(dm73 STATIC
    src/dm73_reader.cpp
    src/frag_extractor.cpp
    ${VENDOR_SRCS}
)

target_include_directories(dm73 PUBLIC
    include/
    vendor/
)

# Disable warnings from vendored C sources (we don't own them)
set_source_files_properties(${VENDOR_SRCS} PROPERTIES
    COMPILE_FLAGS "-w"
)

# ---------------------------------------------------------------------------
# CLI tool: dm73dump
# ---------------------------------------------------------------------------
add_executable(dm73dump src/main.cpp)
target_link_libraries(dm73dump dm73)

# ---------------------------------------------------------------------------
# Install targets
# ---------------------------------------------------------------------------
install(TARGETS dm73dump DESTINATION bin)
install(TARGETS dm73 DESTINATION lib)
install(DIRECTORY include/ DESTINATION include/dm73)

# ---------------------------------------------------------------------------
# Tests (optional — requires Python + pytest, not built by CMake)
# Run: pytest tests/
# ---------------------------------------------------------------------------
