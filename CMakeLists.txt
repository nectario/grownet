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

# Collect .cpp sources for the library, but exclude demo
file(GLOB_RECURSE GROWNET_ALL_CPP "${GROWNET_CPP_ROOT}/*.cpp")
set(GROWNET_LIB_SOURCES ${GROWNET_ALL_CPP})
foreach(_src IN LISTS GROWNET_ALL_CPP)
    if(_src MATCHES "/demo/")
        list(REMOVE_ITEM GROWNET_LIB_SOURCES "${_src}")
    endif()
endforeach()

if(NOT GROWNET_LIB_SOURCES)
    message(FATAL_ERROR "No library sources found under ${GROWNET_CPP_ROOT}. \
Make sure your .cpp files are placed there or adjust GROWNET_CPP_ROOT.")
endif()

add_library(grownet ${GROWNET_LIB_SOURCES})
target_include_directories(grownet PUBLIC
        "${GROWNET_CPP_ROOT}"
        "${GROWNET_CPP_ROOT}/grownet"
)

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
