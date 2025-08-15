// Suggested location: src/cpp/bench/bench_main.cpp
// Build: add this file to your CMake target or a new executable target "bench_grownet".
// Usage: bench_grownet --scenario image_64x64 --json --params '{"frames":100,"height":64,"width":64}'

#include <chrono>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <memory>
#include <random>
#include <string>
#include <unordered_map>
#include <vector>
#include <sstream>

#include "Region.h"
#include "Layer.h"
#include "InputLayer2D.h"
#include "OutputLayer2D.h"

using namespace grownet;
using clock_type = std::chrono::high_resolution_clock;

static std::unordered_map<std::string, std::string> parse_args(int argc, char** argv) {
    std::unordered_map<std::string, std::string> m;
    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        if (a == "--scenario" && i + 1 < argc) m["scenario"] = argv[++i];
        else if (a == "--json") m["json"] = "1";
        else if (a == "--params" && i + 1 < argc) m["params"] = argv[++i];
    }
    return m;
}

int main(int argc, char** argv) {
    auto args = parse_args(argc, argv);
    std::string scenario = args.count("scenario") ? args["scenario"] : "image_64x64";

    // Default params (can be overridden via --params JSON if you want to expand)
    int frames = 100, h = 64, w = 64;
    int excit = 512, inhib = 64, mod = 16;

    Region region("bench_cpp");
    // Build minimal chain: Input2D -> mixed Layer -> Output2D
    auto l_in  = std::make_shared<InputLayer2D>(h, w, 1.0, 0.01);
    auto l_mid = std::make_shared<Layer>(excit, inhib, mod);
    auto l_out = std::make_shared<OutputLayer2D>(h, w, 0.2);

    region.getLayers().push_back(l_in);
    region.getLayers().push_back(l_mid);
    region.getLayers().push_back(l_out);

    // Connect feedforward
    l_mid->wireRandomFeedforward(0.02);
    l_out->wireRandomFeedforward(0.02);

    // E2E measure (image frames)
    std::mt19937 rng(1234);
    std::uniform_real_distribution<double> uni(0.0, 1.0);

    auto t0 = clock_type::now();
    for (int f = 0; f < frames; ++f) {
        std::vector<std::vector<double>> frame(h, std::vector<double>(w));
        for (int y = 0; y < h; ++y) for (int x = 0; x < w; ++x) frame[y][x] = uni(rng);
        // Assuming Region has tickImage(port, frame) and an input port named "pixels"
        region.tickImage("pixels", frame);
    }
    auto t1 = clock_type::now();
    double ms = std::chrono::duration<double, std::milli>(t1 - t0).count();

    // Minimal JSON (extend with RegionMetrics if you collect them)
    std::ostringstream oss;
    oss << "{"
        << "\"impl\":\"cpp\","
        << "\"scenario\":\"" << scenario << "\","
        << "\"runs\":1,"
        << "\"metrics\":{"
        << "\"e2e_wall_ms\":" << ms << ","
        << "\"ticks\":" << frames << ","
        << "\"per_tick_us_avg\":" << (ms * 1000.0 / frames)
        << "}}";
    std::cout << oss.str() << std::endl;
    return 0;
}
