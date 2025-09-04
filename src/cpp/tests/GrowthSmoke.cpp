// Compile only when explicitly enabled to keep production builds clean.
#ifdef GROWNET_GROWTH_SMOKE
#include "Region.h"
#include <iostream>

int main() {
    using namespace grownet;
    Region region("growth-smoke");

    int in  = region.addInputLayer2D(4, 4, 1.0, 0.01);
    int hid = region.addLayer(4, 0, 0);
    int out = region.addOutputLayer2D(4, 4, 0.0);

    // Deterministic windowed wiring + sparse feedforward
    region.connectLayersWindowed(in, hid, 2, 2, 2, 2, "valid", false);
    region.connectLayers(hid, out, 0.5, false);
    region.bindInput("img", { in });

    std::vector<std::vector<double>> f1(4, std::vector<double>(4, 0.0));
    f1[0][1] = 1.0; region.tickImage("img", f1);
    std::vector<std::vector<double>> f2(4, std::vector<double>(4, 0.0));
    f2[0][2] = 1.0; region.tickImage("img", f2);

    std::cout << "[OK] Growth smoke executed." << std::endl;
    return 0;
}
#endif

