#include <gtest/gtest.h>
#include "Region.h"

using namespace grownet;

TEST(WindowedWiringReattach, ReattachNewSourceOnGrowth) {
    Region region("test");
    const int src = region.addInputLayer2D(4, 4, 1.0, 0.0);
    const int dst = region.addOutputLayer2D(4, 4, 0.0);
    (void)region.connectLayersWindowed(src, dst, 3, 3, 1, 1, "same", false);

    // Autowire for a hypothetical new source neuron index; smoke test that it does not throw.
    region.autowireNewNeuron(region.getLayers()[src].get(), /*newNeuronIndex*/ 5);
    SUCCEED();
}

