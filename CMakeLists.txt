
cmake_minimum_required(VERSION 3.16)
project(GrowNetCpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(grownet
    src/Weight.cpp
    src/Synapse.cpp
    src/LateralBus.cpp
    src/RegionBus.cpp
    src/Neuron.cpp
    src/ExcitatoryNeuron.cpp
    src/InhibitoryNeuron.cpp
    src/ModulatoryNeuron.cpp
    src/Layer.cpp
    src/Tract.cpp
    src/Region.cpp
)

target_include_directories(grownet PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)

add_executable(demo src/DemoMain.cpp)
target_link_libraries(demo PRIVATE grownet)
