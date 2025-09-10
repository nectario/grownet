#include <iostream>
#include <vector>
#include <string>
#include "Region.h"

using namespace grownet;

struct WindowConfig {
    int kernelH;
    int kernelW;
    int strideH;
    int strideW;
    std::string padding;
};

static int run_and_print(const WindowConfig& cfg) {
    Region region("windowed_demo");
    const int src = region.addInputLayer2D(16, 16, /*gain*/1.0, /*epsilonFire*/0.0);
    const int dst = region.addOutputLayer2D(16, 16, /*smoothing*/0.0);
    const int uniqueSources = region.connectLayersWindowed(
        src, dst,
        cfg.kernelH, cfg.kernelW,
        cfg.strideH, cfg.strideW,
        cfg.padding, /*feedback*/ false);

    std::cout << "kernel=(" << cfg.kernelH << "x" << cfg.kernelW
              << "), stride=(" << cfg.strideH << "x" << cfg.strideW
              << "), padding=" << cfg.padding
              << "  -> uniqueSources=" << uniqueSources << std::endl;
    return uniqueSources;
}

int main() {
    std::vector<WindowConfig> configs = {
        {3, 3, 1, 1, "same"},
        {5, 5, 1, 1, "same"},
        {7, 7, 2, 2, "same"},
        {3, 3, 2, 2, "valid"}
    };
    for (const auto& cfg : configs) {
        (void)run_and_print(cfg);
    }
    return 0;
}

