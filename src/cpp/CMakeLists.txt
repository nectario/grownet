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
        src/TopographicWiring.cpp
)
target_include_directories(grownet PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}/include)

# ✅ Use DemoMain.cpp (not main.cpp)
add_executable(grownet_demo DemoMain.cpp)
target_link_libraries(grownet_demo PRIVATE grownet)

# Topographic wiring demo
add_executable(topographic_demo demo_topographic.cpp)
target_link_libraries(topographic_demo PRIVATE grownet)

# 2D tick demo
add_executable(two_dim_tick_demo TwoDimTickDemo.cpp)
target_link_libraries(two_dim_tick_demo PRIVATE grownet)
