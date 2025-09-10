#include <iostream>
#include <vector>
#include <string>
#include "Region.h"

using namespace grownet;

int main() {
    try {
        Region region("windowed-parity");
        const int inIndex  = region.addInputLayer2D(16, 16, 1.0, 0.01);
        const int outIndex = region.addOutputLayer2D(16, 16, 0.0);

        struct Combo { int kh, kw, sh, sw; const char* padding; const char* label; };
        std::vector<Combo> combos = {
            {3, 3, 1, 1, "same",  "k3s1-same"},
            {5, 5, 1, 1, "same",  "k5s1-same"},
            {7, 7, 2, 2, "valid", "k7s2-valid"}
        };

        for (const auto& c : combos) {
            int uniqueSources = region.connectLayersWindowed(inIndex, outIndex, c.kh, c.kw, c.sh, c.sw, c.padding, false);
            std::cout << c.label
                      << " -> uniqueSources=" << uniqueSources
                      << " (kernel=" << c.kh << "x" << c.kw
                      << ", stride=" << c.sh << "x" << c.sw
                      << ", padding=" << c.padding << ")\n";
        }
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "Error: " << ex.what() << std::endl;
        return 1;
    }
}

