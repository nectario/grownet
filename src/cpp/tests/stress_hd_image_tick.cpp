#ifdef GTEST_AVAILABLE
#include <gtest/gtest.h>
#endif

#include <vector>
#include <chrono>
#include <iostream>
#include "Region.h"

#ifdef GTEST_AVAILABLE
TEST(StressHDImageTick, One2DTickTiming) {
    grownet::Region region("stress-hd");
    const int H = 1080;
    const int W = 1920;
    // Bind a 2D input edge; do not attach any layers
    region.bindInput2D("img", H, W, /*gain=*/1.0, /*epsilonFire=*/0.01, std::vector<int>{});

    // Build a diagonal pattern
    std::vector<std::vector<double>> frame(H, std::vector<double>(W, 0.0));
    for (int r = 0; r < H; ++r) frame[r][r % W] = 1.0;

    // Warm-up
    region.tick2D("img", frame);

    auto t0 = std::chrono::high_resolution_clock::now();
    auto metrics = region.tick2D("img", frame);
    auto t1 = std::chrono::high_resolution_clock::now();
    auto dt_ms = std::chrono::duration_cast<std::chrono::milliseconds>(t1 - t0).count();
    std::cout << "[C++] HD 1920x1080 tick took ~" << dt_ms << " ms; deliveredEvents=" << metrics.deliveredEvents << std::endl;

    EXPECT_EQ(metrics.deliveredEvents, 1);
}
#endif

