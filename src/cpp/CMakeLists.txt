set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(grownet
        MathUtils.cpp
        LateralBus.cpp
        Weight.cpp
        Synapse.cpp
        Neuron.cpp
        ExcitatoryNeuron.cpp
        InhibitoryNeuron.cpp
        ModulatoryNeuron.cpp
        Layer.cpp
        demo/region_demo.cpp
)
target_include_directories(grownet PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

# ✅ Use DemoMain.cpp (not main.cpp)
add_executable(grownet_demo DemoMain.cpp)
target_link_libraries(grownet_demo PRIVATE grownet)
