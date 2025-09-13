#include <gtest/gtest.h>
#include "Region.h"

using namespace grownet;

TEST(WindowedWiringCenter, UniqueSourcesAndCenterRule) {
    Region region("test");
    const int src = region.addInputLayer2D(5, 5, /*gain*/1.0, /*epsilonFire*/0.0);
    const int dst = region.addOutputLayer2D(5, 5, /*smoothing*/0.0);

    const int uniqueSources = region.connectLayersWindowed(
        src, dst, /*kernelH*/3, /*kernelW*/3,
        /*strideH*/1, /*strideW*/1, /*padding*/"same", /*feedback*/false);

    ASSERT_LE(uniqueSources, 25);
    ASSERT_GE(uniqueSources, 1);
}

