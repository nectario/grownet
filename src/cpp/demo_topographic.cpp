#include "Region.h"
#include "TopographicWiring.h"
#include <iostream>

using namespace grownet;

int main() {
    Region region("topo-demo");
    int src = region.addInputLayer2D(16, 16, 1.0, 0.01);
    int dst = region.addOutputLayer2D(16, 16, 0.0);
    TopographicConfig cfg; cfg.kernelH = 7; cfg.kernelW = 7; cfg.padding = "same"; cfg.weightMode = "gaussian"; cfg.normalizeIncoming = true;
    int unique = connectLayersTopographic(region, src, dst, cfg);
    std::cout << "unique_sources=" << unique << "\n";
    return 0;
}
