#ifdef GTEST_AVAILABLE
#include <gtest/gtest.h>
#endif

#include <vector>
#include "Region.h"
#include "InputLayerND.h"

#ifdef GTEST_AVAILABLE
TEST(NDTickSmoke, DeliveredEventsOne) {
    grownet::Region region("nd-smoke");
    const std::vector<int> shape{2,3};
    region.bindInputND("nd", shape, 1.0, 0.01, std::vector<int>{});
    std::vector<double> flat(6, 0.0);
    auto m = region.tickND("nd", flat, shape);
    EXPECT_EQ(m.getDeliveredEvents(), 1);
}
#endif

