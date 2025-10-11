// Bench (C++) — InputLayer2D -> mixed Layer -> OutputLayer2D
// Build: add this file to your CMake with an executable target, e.g. bench_grownet
// Usage: ./bench_grownet --scenario image_64x64 --json --params '{"frames":100,"height":64,"width":64}'

#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <random>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

#include "Region.h"

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
    std::string scenario = args.count("scenario") ? args["scenario"] : std::string("image_64x64");

    // Defaults
    int frames = 100, h = 64, w = 64;
    int excit = 512, inhib = 64, mod = 16;
    std::string port = "pixels";

    Region region("bench_cpp");
    // Build: bind input edge to mid layer, connect mid->out
    int mid = region.addLayer(excit, inhib, mod);
    int out = region.addOutputLayer2D(h, w, 0.2);
    region.bindInput2D(port, h, w, 1.0, 0.01, std::vector<int>{mid});
    (void)region.connectLayers(mid, out, 0.02, /*feedback=*/false);

    std::mt19937 rng(1234);
    std::uniform_real_distribution<double> uni(0.0, 1.0);
    auto make_frame = [&](int H, int W) {
        std::vector<std::vector<double>> f(H, std::vector<double>(W));
        for (int r = 0; r < H; ++r) {
            for (int c = 0; c < W; ++c) f[r][c] = uni(rng);
        }
        return f;
    };

    // Warmup
    region.tickImage(port, make_frame(h, w));

    auto t0 = clock_type::now();
    long long delivered = 0;
    for (int i = 0; i < frames; ++i) {
        auto m = region.tickImage(port, make_frame(h, w));
        delivered += m.getDeliveredEvents();
    }
    auto t1 = clock_type::now();
    double elapsed_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();

    std::ostringstream oss;
    oss << "{\"impl\":\"cpp\",\"scenario\":\"" << scenario << "\",\"runs\":1,"
        << "\"metrics\":{\"e2e_wall_ms\":" << elapsed_ms << ",\"ticks\":" << frames
        << ",\"per_tick_us_avg\":" << (elapsed_ms * 1000.0 / frames)
        << ",\"delivered_events\":" << delivered << "}}";
    std::cout << oss.str() << std::endl;
    return 0;
}

