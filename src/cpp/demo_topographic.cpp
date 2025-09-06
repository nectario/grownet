#include "Region.h"
#include "TopographicWiring.h"
#include <iostream>

using namespace grownet;

int main() {
    Region region("topo-demo");
    int src = region.addInputLayer2D(16, 16, 1.0, 0.01);
    int dst = region.addOutputLayer2D(16, 16, 0.0);
    TopographicConfig cfg; cfg.kernel_h = 7; cfg.kernel_w = 7; cfg.padding = "same"; cfg.weight_mode = "gaussian"; cfg.normalize_incoming = true;
    int unique = connectLayersTopographic(region, src, dst, cfg);
    std::cout << "unique_sources=" << unique << "\n";
    return 0;
}

