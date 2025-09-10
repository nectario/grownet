#include <iostream>
#include <string>
#include <vector>
#include "Region.h"

using namespace grownet;

static int connectAndCount(Region& region,
                           int sourceIndex,
                           int destIndex,
                           int kernelH, int kernelW,
                           int strideH, int strideW,
                           const std::string& padding) {
    return region.connectLayersWindowed(sourceIndex, destIndex,
                                        kernelH, kernelW, strideH, strideW,
                                        padding, /*feedback=*/false);
}

int main() {
    try {
        Region region("windowed-unique-sources");
        const int inputIndex  = region.addInputLayer2D(16, 16, 1.0, 0.01);
        const int outputIndex = region.addOutputLayer2D(16, 16, 0.0);

        struct Combo { int kh, kw, sh, sw; const char* padding; const char* label; };
        std::vector<Combo> combos = {
            {3, 3, 1, 1, "same",  "k3s1-same"},
            {5, 5, 1, 1, "same",  "k5s1-same"},
            {7, 7, 2, 2, "valid", "k7s2-valid"}
        };

        for (const auto& combo : combos) {
            int uniqueSources = connectAndCount(region, inputIndex, outputIndex,
                                               combo.kh, combo.kw, combo.sh, combo.sw, combo.padding);
            std::cout << combo.label
                      << " -> uniqueSources=" << uniqueSources
                      << " (kernel=" << combo.kh << "x" << combo.kw
                      << ", stride=" << combo.sh << "x" << combo.sw
                      << ", padding=" << combo.padding << ")\n";
        }
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "Error: " << ex.what() << std::endl;
        return 1;
    }
}

