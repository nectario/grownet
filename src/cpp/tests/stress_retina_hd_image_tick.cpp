#ifdef GTEST_AVAILABLE
#include <gtest/gtest.h>
#endif

#include <vector>
#include <chrono>
#include <iostream>
#include "Region.h"
#include "include/TopographicWiring.h"

#ifdef GTEST_AVAILABLE
TEST(StressRetinaHDImageTick, One2DTickTiming) {
    grownet::Region region("stress-retina-hd");
    const int H = 1080;
    const int W = 1920;
    int in  = region.addInputLayer2D(H, W, 1.0, 0.01);
    int out = region.addOutputLayer2D(H, W, 0.0);

    grownet::TopographicConfig cfg;
    cfg.kernel_h = 7; cfg.kernel_w = 7;
    cfg.stride_h = 1; cfg.stride_w = 1;
    cfg.padding = std::string("same");
    cfg.weight_mode = std::string("gaussian");
    cfg.normalize_incoming = true;
    int unique = grownet::connectLayersTopographic(region, in, out, cfg);
    ASSERT_GT(unique, 0);

    region.bindInput2D("img", H, W, 1.0, 0.01, std::vector<int>{in});

    std::vector<std::vector<double>> frame(H, std::vector<double>(W, 0.0));
    for (int r = 0; r < H; ++r) frame[r][r % W] = 1.0;

    region.tick2D("img", frame);

    auto t0 = std::chrono::high_resolution_clock::now();
    auto metrics = region.tick2D("img", frame);
    auto t1 = std::chrono::high_resolution_clock::now();
    auto dt_ms = std::chrono::duration_cast<std::chrono::milliseconds>(t1 - t0).count();
    std::cout << "[C++] Retina HD 1920x1080 tick took ~" << dt_ms << " ms; deliveredEvents=" << metrics.deliveredEvents << std::endl;
    EXPECT_EQ(metrics.deliveredEvents, 1);
}
#endif

