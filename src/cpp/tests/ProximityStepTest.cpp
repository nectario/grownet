#include <gtest/gtest.h>
#include "Region.h"
#include "ProximityConfig.h"

using namespace grownet;

TEST(ProximityStep, ApplyOncePerTickGuard) {
    Region region("prox");
    // Simple graph to ensure layers exist
    const int in = region.addInputLayer2D(3, 3, 1.0, 0.0);
    const int out = region.addOutputLayer2D(3, 3, 0.0);
    (void)region.connectLayers(in, out, 1.0, false);

    // Enable proximity policy (STEP). We will bind a port and tick.
    ProximityConfig config;
    config.proximityConnectEnabled = true;
    config.proximityFunction = ProximityConfig::Function::STEP;
    config.proximityRadius = 1.5;
    config.proximityMaxEdgesPerTick = 4;
    region.setProximityConfig(config);

    // Bind a 2D input port and tick once; guard ensures apply runs at most once per step.
    region.bindInput2D("img", 3, 3, 1.0, 0.0, std::vector<int>{ in });
    std::vector<std::vector<double>> frame(3, std::vector<double>(3, 0.0));
    frame[1][1] = 1.0;
    (void)region.tick2D("img", frame);

    SUCCEED();
}

