cmake_minimum_required(VERSION 3.16)
project(GrowNet CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(MSVC)
    add_compile_options(/W4 /permissive-)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Adjust if your sources live elsewhere
set(GROWNET_CPP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/src/cpp")

# Collect .cpp sources for the library, then exclude tests and demos robustly
file(GLOB_RECURSE GROWNET_ALL_CPP CONFIGURE_DEPENDS "${GROWNET_CPP_ROOT}/*.cpp")
set(GROWNET_LIB_SOURCES ${GROWNET_ALL_CPP})

# Exclude tests/ and demo/ folders from the core library
list(FILTER GROWNET_LIB_SOURCES EXCLUDE REGEX ".*[/\\]tests[/\\].*")
list(FILTER GROWNET_LIB_SOURCES EXCLUDE REGEX ".*[/\\]demo[/\\].*")

# Exclude any top-level demo sources under src/cpp (TwoDimTickDemo.cpp, RegionDemo.cpp, ImageIODemo.cpp, etc.)
list(FILTER GROWNET_LIB_SOURCES EXCLUDE REGEX ".*[/\\](Demo.*|demo_.*|.*Demo.*|.*demo.*)\\.cpp$")
list(FILTER GROWNET_LIB_SOURCES EXCLUDE REGEX ".*[/\\](TwoDimTickDemo|RegionDemo|ImageIODemo|DemoMain)\\.cpp$")

if(NOT GROWNET_LIB_SOURCES)
    message(FATAL_ERROR "No library sources found under ${GROWNET_CPP_ROOT}. \
Make sure your .cpp files are placed there or adjust GROWNET_CPP_ROOT.")
endif()

add_library(grownet ${GROWNET_LIB_SOURCES})
target_include_directories(grownet PUBLIC
        "${GROWNET_CPP_ROOT}"
        "${GROWNET_CPP_ROOT}/grownet"
        "${GROWNET_CPP_ROOT}/include"
)

# --- PAL / OpenMP backend (optional) -----------------------------------------
option(GROWNET_WITH_OPENMP "Enable OpenMP backend for PAL (C++)" ON)
if (GROWNET_WITH_OPENMP)
  find_package(OpenMP)
  if (OpenMP_CXX_FOUND)
    message(STATUS "GrowNet: OpenMP found; enabling PAL parallel backends.")
    if (TARGET grownet)
      target_link_libraries(grownet PUBLIC OpenMP::OpenMP_CXX)
      if (DEFINED OpenMP_CXX_FLAGS)
        target_compile_options(grownet PRIVATE ${OpenMP_CXX_FLAGS})
      endif()
      if (DEFINED OpenMP_CXX_LIBRARIES)
        target_link_libraries(grownet PRIVATE ${OpenMP_CXX_LIBRARIES})
      endif()
      # MinGW-specific: explicitly link libgomp when available
      if (MINGW)
        target_link_libraries(grownet PUBLIC gomp)
      endif()
    endif()
  else()
    message(WARNING "GrowNet: OpenMP not found; PAL will run sequentially.")
  endif()
endif()

# Demo (optional)
set(GROWNET_DEMO "${GROWNET_CPP_ROOT}/demo/region_demo.cpp")
if(EXISTS "${GROWNET_DEMO}")
    add_executable(region_demo "${GROWNET_DEMO}")
    target_link_libraries(region_demo PRIVATE grownet)
    target_include_directories(region_demo PRIVATE
            "${GROWNET_CPP_ROOT}"
            "${GROWNET_CPP_ROOT}/grownet"
    )
else()
    message(WARNING "Demo not built: ${GROWNET_DEMO} was not found.")
endif()

# Windowed parity demo
set(GROWNET_DEMO_WINDOWED "${GROWNET_CPP_ROOT}/demo/DemoWindowedParity.cpp")
if(EXISTS "${GROWNET_DEMO_WINDOWED}")
    add_executable(DemoWindowedParity "${GROWNET_DEMO_WINDOWED}")
    target_link_libraries(DemoWindowedParity PRIVATE grownet)
    target_include_directories(DemoWindowedParity PRIVATE
            "${GROWNET_CPP_ROOT}"
            "${GROWNET_CPP_ROOT}/grownet"
    )
endif()

# Windowed unique sources demo
set(GROWNET_DEMO_WINDOWED_UNIQ "${GROWNET_CPP_ROOT}/demo/DemoWindowedUniqueSources.cpp")
if(EXISTS "${GROWNET_DEMO_WINDOWED_UNIQ}")
    add_executable(DemoWindowedUniqueSources "${GROWNET_DEMO_WINDOWED_UNIQ}")
    target_link_libraries(DemoWindowedUniqueSources PRIVATE grownet)
    target_include_directories(DemoWindowedUniqueSources PRIVATE
            "${GROWNET_CPP_ROOT}"
            "${GROWNET_CPP_ROOT}/grownet"
    )
endif()

# ------------------------ Tests (GTest + CTest) ------------------------
include(CTest)
option(GROWNET_BUILD_TESTS "Build C++ tests for GrowNet" ON)
# Web-friendly guards
option(GROWNET_USE_SYSTEM_GTEST "Use system-installed GTest if available" ON)
option(GROWNET_SKIP_CPP_TESTS  "Skip C++ tests when environment lacks gtest/network" OFF)

# If running in Codex Web, prefer to skip C++ tests by default
if(DEFINED ENV{CODEX_WEB} AND "$ENV{CODEX_WEB}" STREQUAL "1")
  set(GROWNET_SKIP_CPP_TESTS ON CACHE BOOL "" FORCE)
endif()

if(GROWNET_BUILD_TESTS)
    if(GROWNET_SKIP_CPP_TESTS)
        message(STATUS "[Codex Web] Skipping C++ tests (no gtest/network).")
        return()
    endif()
    enable_testing()

    # Try to find a system GTest; otherwise fetch a known-good version.
    if(GROWNET_USE_SYSTEM_GTEST)
        find_package(GTest QUIET)
    else()
        set(GTest_FOUND OFF)
    endif()
    if (NOT GTest_FOUND)
        message(STATUS "GTest not found; fetching via FetchContent")
        include(FetchContent)
        FetchContent_Declare(
            googletest
            URL https://github.com/google/googletest/archive/refs/tags/v1.13.0.zip
            DOWNLOAD_EXTRACT_TIMESTAMP TRUE
        )
        # For MSVC: prevent overriding runtime library selection
        set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
        FetchContent_MakeAvailable(googletest)
    endif()

    # Collect test sources
    file(GLOB GROWNET_TEST_SOURCES "${GROWNET_CPP_ROOT}/tests/*.cpp")
    if(GROWNET_TEST_SOURCES)
        add_executable(grownet_tests ${GROWNET_TEST_SOURCES})
        target_link_libraries(grownet_tests PRIVATE grownet GTest::gtest GTest::gtest_main)
        target_include_directories(grownet_tests PRIVATE
            "${GROWNET_CPP_ROOT}"
            "${GROWNET_CPP_ROOT}/grownet"
        )
        # Ensure OpenMP flags/libraries are applied to tests (MinGW can be picky)
        if (OpenMP_CXX_FOUND)
            target_link_libraries(grownet_tests PUBLIC OpenMP::OpenMP_CXX)
            # Also apply compiler/linker flags explicitly for compatibility across generators
            if (DEFINED OpenMP_CXX_FLAGS)
                target_compile_options(grownet_tests PRIVATE ${OpenMP_CXX_FLAGS})
            endif()
            if (DEFINED OpenMP_CXX_LIBRARIES)
                target_link_libraries(grownet_tests PRIVATE ${OpenMP_CXX_LIBRARIES})
            endif()
            if (MINGW)
                target_link_libraries(grownet_tests PUBLIC gomp)
            endif()
        endif()
        target_compile_definitions(grownet_tests PRIVATE GTEST_AVAILABLE)
        add_test(NAME grownet_tests COMMAND grownet_tests)
    else()
        message(WARNING "No C++ test sources found under ${GROWNET_CPP_ROOT}/tests")
    endif()
endif()
