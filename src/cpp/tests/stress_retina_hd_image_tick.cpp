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
    const int imageHeight = 1080;
    const int imageWidth = 1920;
    int inputLayerIndex  = region.addInputLayer2D(imageHeight, imageWidth, 1.0, 0.01);
    int out = region.addOutputLayer2D(H, W, 0.0);

    grownet::TopographicConfig cfg;
    cfg.kernelH = 7; cfg.kernelW = 7;
    cfg.strideH = 1; cfg.strideW = 1;
    cfg.padding = std::string("same");
    cfg.weightMode = std::string("gaussian");
    cfg.normalizeIncoming = true;
    int unique = grownet::connectLayersTopographic(region, in, out, cfg);
    ASSERT_GT(unique, 0);

    region.bindInput2D("img", H, W, 1.0, 0.01, std::vector<int>{in});

    std::vector<std::vector<double>> frame(imageHeight, std::vector<double>(imageWidth, 0.0));
    for (int rowIndex = 0; rowIndex < imageHeight; ++rowIndex) frame[rowIndex][rowIndex % imageWidth] = 1.0;

    region.tick2D("img", frame);

    auto t0 = std::chrono::high_resolution_clock::now();
    auto metrics = region.tick2D("img", frame);
    auto t1 = std::chrono::high_resolution_clock::now();
    auto dt_ms = std::chrono::duration_cast<std::chrono::milliseconds>(t1 - t0).count();
    std::cout << "[C++] Retina HD 1920x1080 tick took ~" << dt_ms << " ms; deliveredEvents=" << metrics.deliveredEvents << std::endl;
    EXPECT_EQ(metrics.deliveredEvents, 1);
}
#endif
