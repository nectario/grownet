#include <iostream>
#include <string>
#include <vector>
#include "Region.h"

using namespace grownet;

static int connect_and_count(Region& region,
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
        const int inIdx  = region.addInputLayer2D(16, 16, 1.0, 0.01);
        const int outIdx = region.addOutputLayer2D(16, 16, 0.0);

        struct Combo { int kh, kw, sh, sw; const char* pad; const char* label; };
        std::vector<Combo> combos = {
            {3, 3, 1, 1, "same",  "k3s1-same"},
            {5, 5, 1, 1, "same",  "k5s1-same"},
            {7, 7, 2, 2, "valid", "k7s2-valid"},
        };

        for (const auto& c : combos) {
            int unique = connect_and_count(region, inIdx, outIdx, c.kh, c.kw, c.sh, c.sw, c.pad);
            std::cout << c.label
                      << " -> uniqueSources=" << unique
                      << " (kernel=" << c.kh << "x" << c.kw
                      << ", stride=" << c.sh << "x" << c.sw
                      << ", padding=" << c.pad << ")\n";
        }
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "Error: " << ex.what() << std::endl;
        return 1;
    }
}

